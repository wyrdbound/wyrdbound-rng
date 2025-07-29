"""
Name class representing a name with its syllable components.
"""

from .segmenters.fantasy_name_segmenter import FantasyNameSegmenter


class Name:
    """
    Represents a name that has been segmented into syllables.
    """

    def __init__(self, name, segmenter=None):
        """
        Initialize a name with syllable segmentation.

        Args:
            name (str): The name to segment
            segmenter: The segmenter to use (defaults to FantasyNameSegmenter)
        """
        self.segmenter = segmenter or FantasyNameSegmenter()
        self._name = None
        self.syllables = []
        self.name = name  # Uses the setter to segment

    @property
    def name(self):
        """Get the name."""
        return self._name

    @name.setter
    def name(self, value):
        """Set the name and segment it into syllables."""
        # Segment the name into syllables
        self.syllables = self.segmenter.segment(value)
        self._name = value

    @property
    def raw_name(self):
        """Get the name with syllable separators."""
        return "/".join(str(s) for s in self.syllables).capitalize()

    def __str__(self):
        """Return the name as a string."""
        return self.name

    def __len__(self):
        """Return the length of the name."""
        return len(self.name)

    def __repr__(self):
        return f"Name('{self.name}')"
