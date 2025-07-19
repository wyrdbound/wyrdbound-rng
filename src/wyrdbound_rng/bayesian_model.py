"""
Bayesian model for computing syllable transition probabilities.
"""

import hashlib
import os
import random
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
from .cache.json_cache_adapter import JsonCacheAdapter
from .cache.cache_adapter import CacheAdapter


class BayesianModel:
    """
    Bayesian model for generating names based on syllable transition probabilities.

    This model computes the probability of syllable transitions from a corpus
    of names and uses these probabilities to generate new names that follow
    the same statistical patterns.
    """

    def __init__(self, cache_adapter: Optional[CacheAdapter] = None):
        """
        Initialize the Bayesian model.

        Args:
            cache_adapter (Optional[CacheAdapter]): Cache adapter for storing probabilities
        """
        self.cache_adapter = cache_adapter or JsonCacheAdapter()

        # Transition probabilities: bigram_probs[syllable1][syllable2] = probability
        self.bigram_probs: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Starting syllable probabilities
        self.start_probs: Dict[str, float] = {}

        # Ending syllable probabilities
        self.end_probs: Dict[str, float] = {}

        # All unique syllables
        self.syllables: List[str] = []

        # Smoothing parameter for Laplace smoothing
        # Reduced from 1.0 to 0.01 to make impossible transitions much less likely
        self.smoothing_alpha = 0.01

        # Cache metadata
        self._cache_key: Optional[str] = None
        self._is_trained = False

    def _compute_cache_key(self, names_file: str, segmenter_type: str) -> str:
        """
        Compute a cache key based on file content and segmenter type.

        Args:
            names_file (str): Path to the names file
            segmenter_type (str): Type of segmenter being used

        Returns:
            str: A unique cache key
        """
        # Get file modification time and size for quick check
        stat = os.stat(names_file)
        file_info = f"{stat.st_mtime}_{stat.st_size}"

        # Create hash of file info, segmenter type, and model version
        cache_input = f"{file_info}_{segmenter_type}_v1.0"
        return hashlib.md5(cache_input.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> bool:
        """
        Load probabilities from cache if available.

        Args:
            cache_key (str): The cache key to load

        Returns:
            bool: True if successfully loaded from cache, False otherwise
        """
        cached_data = self.cache_adapter.get(cache_key)

        if cached_data is None:
            return False

        try:
            self.bigram_probs = defaultdict(dict, cached_data.get("bigram_probs", {}))
            self.start_probs = cached_data.get("start_probs", {})
            self.end_probs = cached_data.get("end_probs", {})
            self.syllables = cached_data.get("syllables", [])
            self._is_trained = True
            return True
        except (KeyError, TypeError):
            # Cache data is corrupted
            return False

    def _save_to_cache(self, cache_key: str) -> None:
        """
        Save current probabilities to cache.

        Args:
            cache_key (str): The cache key to save under
        """
        # Convert defaultdict to regular dict for JSON serialization
        bigram_dict = {k: dict(v) for k, v in self.bigram_probs.items()}

        cache_data = {
            "bigram_probs": bigram_dict,
            "start_probs": self.start_probs,
            "end_probs": self.end_probs,
            "syllables": self.syllables,
        }

        self.cache_adapter.set(cache_key, cache_data)

    def train(self, names: List, names_file: str, segmenter_type: str) -> None:
        """
        Train the model on a corpus of names.

        Args:
            names (List): List of Name objects with syllables
            names_file (str): Path to the original names file
            segmenter_type (str): Type of segmenter used
        """
        # Compute cache key
        cache_key = self._compute_cache_key(names_file, segmenter_type)
        self._cache_key = cache_key

        # Try to load from cache first
        if self._load_from_cache(cache_key):
            print(
                f"Loaded Bayesian probabilities from cache ({len(self.syllables)} syllables)"
            )
            return

        print("Computing Bayesian probabilities...")

        # Extract all syllables and build transition counts
        syllable_set = set()
        bigram_counts = defaultdict(Counter)
        start_counts = Counter()
        end_counts = Counter()

        for name in names:
            name_syllables = [str(syl) for syl in name.syllables]

            if not name_syllables:
                continue

            # Add syllables to our set
            syllable_set.update(name_syllables)

            # Count start syllables
            start_counts[name_syllables[0]] += 1

            # Count end syllables
            end_counts[name_syllables[-1]] += 1

            # Count bigram transitions
            for i in range(len(name_syllables) - 1):
                current_syl = name_syllables[i]
                next_syl = name_syllables[i + 1]
                bigram_counts[current_syl][next_syl] += 1

        self.syllables = sorted(list(syllable_set))
        vocab_size = len(self.syllables)

        # Convert counts to probabilities with Laplace smoothing

        # Start probabilities
        total_starts = sum(start_counts.values())
        for syllable in self.syllables:
            count = start_counts.get(syllable, 0)
            self.start_probs[syllable] = (count + self.smoothing_alpha) / (
                total_starts + vocab_size * self.smoothing_alpha
            )

        # End probabilities
        total_ends = sum(end_counts.values())
        for syllable in self.syllables:
            count = end_counts.get(syllable, 0)
            self.end_probs[syllable] = (count + self.smoothing_alpha) / (
                total_ends + vocab_size * self.smoothing_alpha
            )

        # Bigram transition probabilities
        for current_syl in self.syllables:
            total_transitions = sum(bigram_counts[current_syl].values())

            for next_syl in self.syllables:
                count = bigram_counts[current_syl].get(next_syl, 0)
                # Laplace smoothing
                probability = (count + self.smoothing_alpha) / (
                    total_transitions + vocab_size * self.smoothing_alpha
                )
                self.bigram_probs[current_syl][next_syl] = probability

        self._is_trained = True

        # Save to cache
        self._save_to_cache(cache_key)

        print(f"Computed probabilities for {vocab_size} syllables")

    def _weighted_random_choice(self, probabilities: Dict[str, float]) -> str:
        """
        Choose a random item based on weighted probabilities.

        Args:
            probabilities (Dict[str, float]): Dictionary of item -> probability

        Returns:
            str: The chosen item
        """
        items = list(probabilities.keys())
        weights = list(probabilities.values())

        # Use random.choices for weighted selection
        return random.choices(items, weights=weights, k=1)[0]

    def generate_syllable_sequence(self, max_syllables: int = 5) -> List[str]:
        """
        Generate a sequence of syllables using the trained probabilities.

        Args:
            max_syllables (int): Maximum number of syllables to generate

        Returns:
            List[str]: List of syllables forming a name
        """
        if not self._is_trained:
            raise RuntimeError("Model must be trained before generating sequences")

        if not self.syllables:
            raise RuntimeError("No syllables available for generation")

        sequence = []

        # Choose starting syllable based on start probabilities
        current_syllable = self._weighted_random_choice(self.start_probs)
        sequence.append(current_syllable)

        # Generate subsequent syllables
        for _ in range(max_syllables - 1):
            # Get transition probabilities from current syllable
            next_probs = self.bigram_probs.get(current_syllable, {})

            if not next_probs:
                # Fallback to uniform distribution if no transitions found
                next_probs = {syl: 1.0 / len(self.syllables) for syl in self.syllables}

            # Choose next syllable
            next_syllable = self._weighted_random_choice(next_probs)
            sequence.append(next_syllable)
            current_syllable = next_syllable

            # Check if we should end based on end probabilities
            end_probability = self.end_probs.get(current_syllable, 0.1)
            if random.random() < end_probability and len(sequence) >= 2:
                break

        return sequence

    def calculate_name_probability(self, syllables: List[str]) -> float:
        """
        Calculate the probability of a given syllable sequence.

        Args:
            syllables (List[str]): List of syllables forming a name

        Returns:
            float: The probability of this name given the trained model
        """
        if not self._is_trained or not syllables:
            return 0.0

        # Start with the probability of the first syllable
        probability = self.start_probs.get(syllables[0], 0.0)

        # Multiply by transition probabilities
        for i in range(len(syllables) - 1):
            current_syl = syllables[i]
            next_syl = syllables[i + 1]
            transition_prob = self.bigram_probs.get(current_syl, {}).get(next_syl, 0.0)
            probability *= transition_prob

        # Multiply by end probability of the last syllable
        if len(syllables) > 0:
            end_prob = self.end_probs.get(syllables[-1], 0.0)
            probability *= end_prob

        return probability

    def calculate_normalized_name_probability(self, syllables: List[str]) -> float:
        """
        Calculate the length-normalized probability of a given syllable sequence.

        This uses geometric mean to normalize for sequence length, making probabilities
        comparable across names of different lengths.

        Args:
            syllables (List[str]): List of syllables forming a name

        Returns:
            float: The length-normalized probability of this name
        """
        if not self._is_trained or not syllables:
            return 0.0

        raw_probability = self.calculate_name_probability(syllables)

        if raw_probability <= 0:
            return 0.0

        # Use geometric mean to normalize for length
        # For a sequence of length n, we take the nth root of the probability
        # This makes probabilities comparable across different name lengths
        num_components = len(syllables) + 1  # +1 for the end probability
        normalized_probability = raw_probability ** (1.0 / num_components)

        return normalized_probability

    def get_probability_info(self, syllable: str) -> Dict[str, float]:
        """
        Get probability information for a specific syllable.

        Args:
            syllable (str): The syllable to get info for

        Returns:
            Dict[str, float]: Dictionary with probability information
        """
        if not self._is_trained:
            return {}

        info = {
            "start_probability": self.start_probs.get(syllable, 0.0),
            "end_probability": self.end_probs.get(syllable, 0.0),
        }

        # Add top 5 transition probabilities
        transitions = self.bigram_probs.get(syllable, {})
        sorted_transitions = sorted(
            transitions.items(), key=lambda x: x[1], reverse=True
        )

        for i, (next_syl, prob) in enumerate(sorted_transitions[:5]):
            info[f"top_transition_{i+1}"] = f"{next_syl} ({prob:.3f})"

        return info
