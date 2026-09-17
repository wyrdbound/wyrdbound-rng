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

    def __init__(self, name_source, segmenter=None):
        """
        Initialize the generator with a name source.

        Args:
            name_source (str): Name list identifier (e.g., "generic-fantasy") or
                path to YAML file
            segmenter: Segmenter class to use (defaults to FantasyNameSegmenter)

        Raises:
            FileNotFoundError: If the name source cannot be resolved to a valid file
        """
        self.segmenter = segmenter or FantasyNameSegmenter()

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

        # Initialize Bayesian model (lazy loading)
        self.bayesian_model = None

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
        self, n, max_chars=15, algorithm="very_simple", min_probability_threshold=1.0e-8
    ):
        """
        Generate multiple random names.

        Args:
            n (int): Number of names to generate
            max_chars (int): Maximum character length for names
            algorithm (str): Algorithm to use ('very_simple', 'simple', 'bayesian')
            min_probability_threshold (float): Minimum probability threshold for
                bayesian generation

        Returns:
            list: List of GeneratedName objects
        """
        names = []
        for _ in range(n):
            name = None
            attempts = 0
            while attempts < 100:
                name = self.generate_name(
                    max_chars, algorithm, min_probability_threshold
                )
                if len(name.name) <= max_chars:
                    break
                attempts += 1
            if name:
                names.append(name)
        return names

    def generate_name(
        self, max_len, algorithm="very_simple", min_probability_threshold=1.0e-8
    ):
        """
        Generate a single random name.

        Args:
            max_len (int): Maximum length for the name
            algorithm (str): Algorithm to use
            min_probability_threshold (float): Minimum probability threshold for
                bayesian generation

        Returns:
            GeneratedName: A generated name object
        """
        if algorithm == "very_simple":
            return self._generate_name_very_simple(max_len)
        elif algorithm == "simple":
            return self._generate_name_simple(max_len)
        elif algorithm == "bayesian":
            return self._generate_name_bayesian(max_len, min_probability_threshold)
        else:
            # Default fallback
            return self._generate_name_simple(max_len)

    def _generate_name_very_simple(self, max_len):
        """
        Generate a name using the very simple algorithm (exactly two syllables).

        Args:
            max_len (int): Maximum length for the name

        Returns:
            GeneratedName: A generated name object
        """
        source_names = []
        beginning = ""
        ending = ""

        # Validate maximum length
        if max_len < 2:
            max_len = 2

        # Select a beginning syllable
        attempts = 0
        while attempts < 100:
            name = random.choice(self.names)
            if name.syllables:
                beginning = str(name.syllables[0]).capitalize()
                if len(beginning) < max_len:
                    source_names.append(name.name)
                    break
            attempts += 1

        # Select an ending syllable
        attempts = 0
        while attempts < 100:
            name = random.choice(self.names)
            if name.syllables:
                ending = str(name.syllables[-1])
                candidate = self._remove_repetitions(beginning + ending)
                if len(candidate) <= max_len and self._is_pronounceable(candidate):
                    source_names.append(name.name)
                    break
            attempts += 1

        full_name = self._remove_repetitions(beginning + ending).capitalize()
        return GeneratedName(full_name, source_names, self.segmenter)

    def _generate_name_simple(self, max_len):
        """
        Generate a name using the simple algorithm (variable syllables).

        Args:
            max_len (int): Maximum length for the name

        Returns:
            GeneratedName: A generated name object
        """
        source_names = []
        beginning = ""
        middle = ""
        ending = ""

        # Validate maximum length
        if max_len < 2:
            max_len = 2

        # Select a beginning syllable
        attempts = 0
        while attempts < 100:
            name = random.choice(self.names)
            if name.syllables:
                beginning = str(name.syllables[0]).capitalize()
                if len(beginning) < max_len:
                    source_names.append(name.name)
                    break
            attempts += 1

        # Select an ending syllable
        attempts = 0
        while attempts < 100:
            name = random.choice(self.names)
            if name.syllables:
                ending = str(name.syllables[-1])
                if len(beginning + ending) <= max_len:
                    source_names.append(name.name)
                    break
            attempts += 1

        # Generate zero or more intermediate syllables
        attempts = 0
        while attempts < 100:
            middle = ""
            temp_source_names = []

            # Determine number of intermediate syllables (0-3)
            num_intermediate = random.randint(0, 3)

            for _ in range(num_intermediate):
                name = random.choice(self.names)
                if name.syllables:
                    temp_source_names.append(name.name)
                    syllable = random.choice(name.syllables)
                    middle += str(syllable)

            candidate = self._remove_repetitions(beginning + middle + ending)
            if len(candidate) <= max_len and self._is_pronounceable(candidate):
                source_names.extend(temp_source_names)
                break
            attempts += 1

        full_name = self._remove_repetitions(beginning + middle + ending).capitalize()
        return GeneratedName(full_name, source_names, self.segmenter)

    def _generate_name_bayesian(self, max_len, min_probability_threshold=1.0e-8):
        """
        Generate a name using the Bayesian algorithm (probabilistic syllable
        transitions).

        Args:
            max_len (int): Maximum length for the name
            min_probability_threshold (float): Minimum probability threshold for
                filtering

        Returns:
            GeneratedName: A generated name object
        """
        # Initialize Bayesian model if not already done
        if self.bayesian_model is None:
            self.bayesian_model = BayesianModel()
            segmenter_type = type(self.segmenter).__name__
            self.bayesian_model.train(self.names, self.filename, segmenter_type)

        # Validate maximum length
        if max_len < 2:
            max_len = 2

        # Syllable ceiling derived from the corpus's mean syllable length
        # (the ancestry corpora average ~2.45), not a hardcoded 3.
        max_syllables = self._syllable_budget(max_len)

        # Minimum probability threshold to filter out very low-quality names
        # min_probability_threshold = 1.0e-8

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
                full_name = "".join(syllables)
                full_name = self._remove_repetitions(full_name).capitalize()

                if len(full_name) <= max_len and self._is_pronounceable(full_name):
                    # Calculate normalized probability for this name
                    raw_probability = self.bayesian_model.calculate_name_probability(
                        syllables
                    )
                    normalized_probability = (
                        self.bayesian_model.calculate_normalized_name_probability(
                            syllables
                        )
                    )

                    # Apply minimum probability threshold
                    if raw_probability >= min_probability_threshold:
                        # Success! Return this high-quality Bayesian name
                        return GeneratedName(
                            full_name, [], self.segmenter, normalized_probability
                        )
                    else:
                        # Keep track of the best name we've seen, even if below
                        # threshold
                        if normalized_probability > best_probability:
                            best_name = GeneratedName(
                                full_name, [], self.segmenter, normalized_probability
                            )
                            best_probability = normalized_probability

            except Exception:
                # If syllable generation fails, just try again
                pass

            attempts += 1

        # If we've tried many times and still can't meet the threshold,
        # return the best Bayesian name we found, or fall back to simple algorithm
        if best_name is not None:
            return best_name

        # Last resort: fall back to simple algorithm but add probability calculation
        fallback_name = self._generate_name_simple(max_len)
        if self.bayesian_model and hasattr(fallback_name, "name"):
            syllables = self.segmenter.segment(fallback_name.name)
            syllable_strs = [str(s) for s in syllables]
            probability = self.bayesian_model.calculate_normalized_name_probability(
                syllable_strs
            )
            fallback_name.probability = probability
        return fallback_name

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

    def _is_pronounceable(self, name):
        """
        Reject names containing a run of four or more consecutive consonants.

        The segmenter emits onset-only syllables (``hr``, ``sv``, ``thj``) that
        are legal before a vowel (``hr`` + ``afn`` = Hrafn) and broken before a
        consonant (``hr`` + ``gils`` = Hrgils). ``y`` counts as a vowel so the
        Welsh names in ``ancestry-elf-*`` survive (Gwyn, Myrddin, Bryn).

        Args:
            name (str): Name to check

        Returns:
            bool: True if the name has no four-consonant run
        """
        return re.search(r"[^aeiouy]{4,}", name.lower()) is None

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
