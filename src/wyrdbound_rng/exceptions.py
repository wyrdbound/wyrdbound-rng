"""
Exception classes for the RNG package.
"""


class FileLoadError(Exception):
    """Raised when there's an error loading a name file."""

    pass


class SegmentError(Exception):
    """Raised when a name cannot be segmented into syllables."""

    def __init__(self, original_name, current_name):
        super().__init__(
            f"Cannot segment name '{original_name.capitalize()}'. "
            f"It is likely that a required syllable is missing at '{current_name}'."
        )
        self.original_name = original_name
        self.current_name = current_name
