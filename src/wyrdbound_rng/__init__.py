"""
Wyrdbound Random Name Generator

A comprehensive random name generator library for tabletop RPGs.
Generates random names from a corpus of input names by breaking them into syllables
and recombining them using various algorithms including Bayesian analysis.

This library is designed for use in wyrdbound, a text-based RPG system that emphasizes
narrative and player choice.
"""

__version__ = "1.0.0"
__author__ = "The Wyrd One"

from .generator import Generator
from .name import Name
from .generated_name import GeneratedName
from .syllable import Syllable
from .name_file_loader import NameFileLoader
from .segmenters.fantasy_name_segmenter import FantasyNameSegmenter
from .segmenters.japanese_name_segmenter import JapaneseNameSegmenter
from .evaluator import Evaluator
from .statistics import Statistics
from .syllable_stats import SyllableStats
from .bayesian_model import BayesianModel
from .exceptions import FileLoadError, SegmentError

__all__ = [
    "Generator",
    "Name",
    "GeneratedName",
    "Syllable",
    "NameFileLoader",
    "FantasyNameSegmenter",
    "JapaneseNameSegmenter",
    "Evaluator",
    "Statistics",
    "SyllableStats",
    "BayesianModel",
    "FileLoadError",
    "SegmentError",
]
