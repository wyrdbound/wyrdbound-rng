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

from .bayesian_model import BayesianModel
from .evaluator import Evaluator
from .exceptions import FileLoadError, SegmentError
from .generated_name import GeneratedName
from .generator import Generator
from .name import Name
from .name_file_loader import NameFileLoader
from .segmenters.fantasy_name_segmenter import FantasyNameSegmenter
from .segmenters.japanese_name_segmenter import JapaneseNameSegmenter
from .statistics import Statistics
from .syllable import Syllable
from .syllable_stats import SyllableStats

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
