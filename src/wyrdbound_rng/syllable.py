"""
Syllable class representing a phonetic syllable with initial, inner, and final components.
"""


class Syllable:
    """
    Represents a syllable with initial consonant(s), inner vowel(s), and final consonant(s).
    """

    def __init__(self, initial, inner, final=""):
        """
        Initialize a syllable.

        Args:
            initial (str): Initial consonant sound(s)
            inner (str): Inner vowel sound(s)
            final (str): Final consonant sound(s), optional
        """
        self.initial = initial.lower()
        self.inner = inner.lower()
        self.final = final.lower()

    def __str__(self):
        """Return the complete syllable as a string."""
        return self.initial + self.inner + self.final

    def __repr__(self):
        return f"Syllable('{self.initial}', '{self.inner}', '{self.final}')"
