"""
Main generator class for creating random names.
"""

import random
import re
from typing import Dict

from .bayesian_model import BayesianModel
from .generated_name import GeneratedName
from .name_file_loader import NameFileLoader
from .name_list_resolver import resolve_name_list
from .segmenters.fantasy_name_segmenter import FantasyNameSegmenter


class Generator:
    """
    Main class for generating random names from a corpus of input names.
    """

    def __init__(self, name_source, segmenter=None, rng=None):
        """
        Initialize the generator with a name source.

        Args:
            name_source (str): Name list identifier (e.g., "generic-fantasy") or
                path to YAML file
            segmenter: Segmenter class to use (defaults to FantasyNameSegmenter)
            rng (random.Random, optional): Random source for generation. Defaults
                to the module-level ``random``, preserving existing behavior. A
                consumer with its own derived streams injects an instance.

        Raises:
            FileNotFoundError: If the name source cannot be resolved to a valid file
        """
        self.segmenter = segmenter or FantasyNameSegmenter()
        self.rng = rng if rng is not None else random

        # Resolve the name source to a file path
        self.filename = resolve_name_list(name_source)
        if not self.filename:
            raise FileNotFoundError(
                f"Could not resolve name source '{name_source}' to a valid file"
            )

        self.name_source = name_source  # Store original identifier for reference

        # Load the names from file
        loader = NameFileLoader(self.segmenter)
        self.names = loader.load(self.filename)

        # Mean syllable length drives the syllable budget at generation time;
        # the corpora average ~2.45 characters, not the hardcoded 3.
        all_syllables = [
            str(syllable) for name in self.names for syllable in name.syllables
        ]
        self.mean_syllable_length = (
            sum(len(syllable) for syllable in all_syllables) / len(all_syllables)
            if all_syllables
            else 3.0
        )

        # The phonotactic inventory the name-validity rule is derived from.
        self._cluster_inventory = self._build_cluster_inventory()

        # Initialize Bayesian model (lazy loading)
        self.bayesian_model = None

    CONSONANT_RUN = re.compile(r"[^aeiouy]+")

    # Below this many names a corpus is too sparse to derive a rule from; the
    # four-consonant heuristic is the fallback. generic-fantasy-male has 17
    # names and 27 clusters, generic-fantasy-female 13 and 16, while every
    # corpus at or above 200 names has an inventory rich enough to use.
    MIN_NAMES_FOR_INVENTORY = 100

    def _clusters_by_position(self, name):
        """
        Inter-nuclear consonant clusters, by position class.

        The unit is the run of consonants between one vowel and the next, plus
        the word-initial and word-final runs. ``y`` is a vowel, or every Welsh
        name in ``ancestry-elf-*`` is one long cluster.

        Args:
            name (str): Name to split

        Returns:
            dict: Lists of clusters under ``initial``, ``medial`` and ``final``
        """
        lowered = name.lower()
        result = {"initial": [], "medial": [], "final": []}
        for match in self.CONSONANT_RUN.finditer(lowered):
            if match.start() == 0:
                result["initial"].append(match.group())
            elif match.end() == len(lowered):
                result["final"].append(match.group())
            else:
                result["medial"].append(match.group())
        return result

    def _build_cluster_inventory(self):
        """
        Build the corpus's cluster inventory, by position class.

        Returns:
            dict: ``initial``/``medial``/``final`` sets, plus ``onset``,
                ``coda``, ``max_length`` and the source ``names`` count. Empty
                when the corpus is below ``MIN_NAMES_FOR_INVENTORY``.
        """
        if len(self.names) < self.MIN_NAMES_FOR_INVENTORY:
            return {}

        observed = {"initial": set(), "medial": set(), "final": set()}
        max_length = 0
        for name in self.names:
            for position, clusters in self._clusters_by_position(name.name).items():
                observed[position].update(clusters)
                for cluster in clusters:
                    max_length = max(max_length, len(cluster))

        return {
            "observed": observed,
            "onset": set(observed["initial"]),
            "coda": set(observed["final"]),
            "max_length": max_length,
            "names": len(self.names),
        }

    def _cluster_is_legal(self, cluster, position):
        """
        Is a cluster legal at a position class?

        Legal if observed at that class, or if it splits at some point into an
        attested onset plus an attested coda in either order. The length
        backstop rejects anything longer than the longest observed cluster:
        decomposition alone would accept an arbitrarily long chain of pieces.

        Args:
            cluster (str): The inter-nuclear cluster
            position (str): ``initial``, ``medial`` or ``final``

        Returns:
            bool: True if the cluster is legal
        """
        inventory = self._cluster_inventory
        if not inventory:
            return True

        if len(cluster) > inventory["max_length"]:
            return False
        if cluster in inventory["observed"][position]:
            return True

        onset = inventory["onset"]
        coda = inventory["coda"]
        for split in range(1, len(cluster)):
            prefix, suffix = cluster[:split], cluster[split:]
            if (prefix in onset and suffix in coda) or (
                prefix in coda and suffix in onset
            ):
                return True
        return False

    def _is_pronounceable(self, name):
        """
        Is the name legal under the corpus's own phonotactics?

        Every inter-nuclear cluster must have been observed in the corpus or
        decompose into an attested onset plus an attested coda. This replaces
        the four-consonant heuristic, which was a no-op and measured the wrong
        unit -- see ``tools/cluster_report.py``.

        A corpus below ``MIN_NAMES_FOR_INVENTORY`` is too sparse to derive a
        rule from, so it falls back to the four-consonant heuristic rather than
        rejecting everything.

        Args:
            name (str): Name to check

        Returns:
            bool: True if every cluster is legal
        """
        if not self._cluster_inventory:
            return re.search(r"[^aeiouy]{4,}", name.lower()) is None

        for position, clusters in self._clusters_by_position(name).items():
            for cluster in clusters:
                if not self._cluster_is_legal(cluster, position):
                    return False
        return True

    def _syllable_budget(self, max_len, mean_syllable_length=None):
        """
        Derive a syllable ceiling from the character cap and the corpus.

        Args:
            max_len (int): Maximum character length for the name
            mean_syllable_length (float): Mean syllable length to use; defaults
                to the loaded corpus's measurement

        Returns:
            int: Maximum syllable count, at least 2
        """
        mean = mean_syllable_length or self.mean_syllable_length
        per_syllable = max(1.0, mean)
        return max(2, int(max_len / per_syllable))

    def generate(
        self,
        n,
        max_chars=15,
        algorithm="very_simple",
        min_probability_threshold=1.0e-8,
        min_len=3,
    ):
        """
        Generate multiple random names.

        Args:
            n (int): Number of names to generate
            max_chars (int): Maximum character length for names
            algorithm (str): Algorithm to use ('very_simple', 'simple', 'bayesian')
            min_probability_threshold (float): Minimum probability threshold for
                bayesian generation
            min_len (int): Minimum character length for names

        Returns:
            list: List of GeneratedName objects
        """
        names = []
        for _ in range(n):
            name = None
            attempts = 0
            while attempts < 100:
                name = self.generate_name(
                    max_chars, algorithm, min_probability_threshold, min_len
                )
                if min_len <= len(name.name) <= max_chars:
                    break
                attempts += 1
            if name:
                names.append(name)
        return names

    def generate_name(
        self,
        max_len,
        algorithm="very_simple",
        min_probability_threshold=1.0e-8,
        min_len=3,
    ):
        """
        Generate a single random name.

        Args:
            max_len (int): Maximum length for the name
            algorithm (str): Algorithm to use
            min_probability_threshold (float): Minimum probability threshold for
                bayesian generation
            min_len (int): Minimum length for the name. Defaults to 3, matching
                the shortest names the existing corpora produce.

        Returns:
            GeneratedName: A generated name object
        """
        if min_len > max_len:
            raise ValueError(f"min_len ({min_len}) must not exceed max_len ({max_len})")

        if algorithm == "very_simple":
            return self._generate_name_very_simple(max_len, min_len)
        elif algorithm == "simple":
            return self._generate_name_simple(max_len, min_len)
        elif algorithm == "bayesian":
            return self._generate_name_bayesian(
                max_len, min_probability_threshold, min_len
            )
        else:
            # Default fallback
            return self._generate_name_simple(max_len, min_len)

    def _generate_name_very_simple(self, max_len, min_len=3):
        """
        Generate a name using the very simple algorithm (exactly two syllables).

        Args:
            max_len (int): Maximum length for the name
            min_len (int): Minimum length for the name

        Returns:
            GeneratedName: A generated name object

        Raises:
            ValueError: If no legal two-syllable name can be assembled
        """
        # Validate maximum length
        if max_len < 2:
            max_len = 2

        for _ in range(100):
            beginning_name = self.rng.choice(self.names)
            if not beginning_name.syllables:
                continue
            beginning = str(beginning_name.syllables[0]).capitalize()

            ending_name = self.rng.choice(self.names)
            if not ending_name.syllables:
                continue
            ending = str(ending_name.syllables[-1])

            candidate = self._remove_repetitions(beginning + ending).capitalize()
            if min_len <= len(candidate) <= max_len and self._is_pronounceable(
                candidate
            ):
                return GeneratedName(
                    candidate,
                    [beginning_name.name, ending_name.name],
                    self.segmenter,
                )

        raise ValueError(
            f"Could not assemble a very_simple name within [{min_len}, {max_len}] "
            "in 100 attempts"
        )

    def _generate_name_simple(self, max_len, min_len=3):
        """
        Generate a name using the simple algorithm (variable syllables).

        Args:
            max_len (int): Maximum length for the name
            min_len (int): Minimum length for the name

        Returns:
            GeneratedName: A generated name object

        Raises:
            ValueError: If no legal name can be assembled
        """
        # Validate maximum length
        if max_len < 2:
            max_len = 2

        for _ in range(100):
            beginning_name = self.rng.choice(self.names)
            if not beginning_name.syllables:
                continue
            beginning = str(beginning_name.syllables[0]).capitalize()

            ending_name = self.rng.choice(self.names)
            if not ending_name.syllables:
                continue
            ending = str(ending_name.syllables[-1])

            # Generate zero or more intermediate syllables
            middle = ""
            temp_source_names = []
            for _ in range(self.rng.randint(0, 3)):
                name = self.rng.choice(self.names)
                if name.syllables:
                    temp_source_names.append(name.name)
                    middle += str(self.rng.choice(name.syllables))

            candidate = self._remove_repetitions(beginning + middle + ending)
            candidate = candidate.capitalize()
            if min_len <= len(candidate) <= max_len and self._is_pronounceable(
                candidate
            ):
                source_names = [beginning_name.name, ending_name.name]
                source_names.extend(temp_source_names)
                return GeneratedName(candidate, source_names, self.segmenter)

        raise ValueError(
            f"Could not assemble a simple name within [{min_len}, {max_len}] "
            "in 100 attempts"
        )

    def _trim_to_length(self, syllables, max_len):
        """
        Greedily trim a syllable sequence to the character cap.

        Trims at a syllable boundary rather than mid-syllable, so the result is
        still a sequence the corpus would produce.

        Args:
            syllables (list): Syllable sequence
            max_len (int): Maximum character length for the name

        Returns:
            list: The longest prefix that fits, possibly empty
        """
        trimmed = []
        for syllable in syllables:
            candidate = self._remove_repetitions("".join(trimmed + [syllable]))
            if len(candidate) > max_len:
                break
            trimmed.append(syllable)
        return trimmed

    def _generate_name_bayesian(
        self, max_len, min_probability_threshold=1.0e-8, min_len=3
    ):
        """
        Generate a name using the Bayesian algorithm (probabilistic syllable
        transitions).

        Args:
            max_len (int): Maximum length for the name
            min_probability_threshold (float): Minimum probability threshold for
                filtering
            min_len (int): Minimum length for the name

        Returns:
            GeneratedName: A generated name object
        """
        # Initialize Bayesian model if not already done
        if self.bayesian_model is None:
            self.bayesian_model = BayesianModel(rng=self.rng)
            segmenter_type = type(self.segmenter).__name__
            self.bayesian_model.train(self.names, self.filename, segmenter_type)

        # Validate maximum length
        if max_len < 2:
            max_len = 2

        # Syllable ceiling derived from the corpus's mean syllable length
        # (the ancestry corpora average ~2.45), not a hardcoded 3.
        max_syllables = self._syllable_budget(max_len)

        attempts = 0
        best_name = None
        best_probability = 0.0
        max_attempts = 500  # Increased attempts for better quality

        while attempts < max_attempts:
            try:
                # Generate syllable sequence
                syllables = self.bayesian_model.generate_syllable_sequence(
                    max_syllables, max_chars=max_len
                )
                if not syllables:
                    attempts += 1
                    continue

                # Join syllables to form name
                full_name = self._remove_repetitions("".join(syllables)).capitalize()

                if len(full_name) > max_len or not self._is_pronounceable(full_name):
                    # Track the best candidate across every rejection reason,
                    # trimming an over-length sequence at a syllable boundary
                    # before giving up on it. The hardest cases no longer fall
                    # through to the simple algorithm.
                    trimmed = self._trim_to_length(syllables, max_len)
                    if not trimmed:
                        attempts += 1
                        continue
                    trimmed_name = self._remove_repetitions(
                        "".join(trimmed)
                    ).capitalize()
                    if not trimmed_name or not self._is_pronounceable(trimmed_name):
                        attempts += 1
                        continue
                    syllables = trimmed
                    full_name = trimmed_name

                if len(full_name) < min_len:
                    attempts += 1
                    continue

                raw_probability = self.bayesian_model.calculate_name_probability(
                    syllables
                )
                normalized_probability = (
                    self.bayesian_model.calculate_normalized_name_probability(syllables)
                )

                # Apply minimum probability threshold
                if raw_probability >= min_probability_threshold:
                    # Success! Return this high-quality Bayesian name
                    return GeneratedName(
                        full_name, [], self.segmenter, normalized_probability
                    )

                # Keep track of the best name we've seen, even if below threshold
                if best_name is None or normalized_probability > best_probability:
                    best_name = GeneratedName(
                        full_name, [], self.segmenter, normalized_probability
                    )
                    best_probability = normalized_probability

            except Exception:
                # If syllable generation fails, just try again
                pass

            attempts += 1

        # Nothing met the threshold; return the highest-probability candidate
        # seen rather than falling back to the simple algorithm.
        if best_name is not None:
            return best_name

        raise RuntimeError(
            f"Bayesian generation produced no candidate within {max_attempts} "
            f"attempts at max_len={max_len}"
        )

    def name_exists_in_corpus(self, name: str) -> bool:
        """
        Check if a name exists in the original corpus.

        Args:
            name (str): The name to check

        Returns:
            bool: True if the name exists in the corpus, False otherwise
        """
        return name.lower() in {str(n).lower() for n in self.names}

    def get_syllable_probability_info(self, syllable: str) -> Dict:
        """
        Get probability information for a specific syllable using the Bayesian model.

        Args:
            syllable (str): The syllable to analyze

        Returns:
            Dict: Dictionary with probability information, or empty dict if not
                available
        """
        # Initialize Bayesian model if not already done
        if self.bayesian_model is None:
            from .bayesian_model import BayesianModel

            self.bayesian_model = BayesianModel()
            segmenter_type = type(self.segmenter).__name__
            self.bayesian_model.train(self.names, self.filename, segmenter_type)

        return self.bayesian_model.get_probability_info(syllable)

    def _remove_repetitions(self, name):
        """
        Collapse runs of repeated letters to a double.

        A run of three or more identical letters becomes two ("Styrrr" ->
        "Styrr"); a double is left alone. The previous implementation deleted
        every "ll" and "nn" outright, which mangled roughly a third of all
        generated names.

        Args:
            name (str): Name to clean up

        Returns:
            str: Cleaned name
        """
        return re.sub(r"(.)\1{2,}", r"\1\1", name)

    def dump_names(self):
        """Print all loaded names for debugging."""
        print("-" * 16 + " " + "-" * 16)
        print(" Name".ljust(16) + " " + " RawName".ljust(16))
        print("-" * 16 + " " + "-" * 16)

        for name in self.names:
            print(name.name.ljust(16) + " " + name.raw_name.ljust(16))

    def dump_syllables(self):
        """Print all unique syllables for debugging."""
        syllables = set()
        for name in self.names:
            for syllable in name.syllables:
                syllables.add(str(syllable))

        syllables = sorted(syllables)

        for i, syllable in enumerate(syllables, 1):
            print(f"{i:4}: {syllable}")
