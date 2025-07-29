"""
Tests for the Name class.
"""

from wyrdbound_rng import Name, Syllable


class TestName:
    """Test cases for the Name class."""

    def test_name_provides_name_field(self):
        """Test that name provides access to the original name string."""
        thorin = Name("Thorin")
        assert thorin.name == "Thorin"

    def test_name_provides_raw_name_with_syllable_separators(self):
        """Test that raw_name provides syllables separated by slashes."""
        thorin = Name("Thorin")
        assert thorin.raw_name == "Tho/rin"

    def test_name_to_string_returns_name(self):
        """Test that str(name) returns the name string."""
        thorin = Name("Thorin")
        assert str(thorin) == thorin.name
        assert str(thorin) == "Thorin"

    def test_name_provides_length_attribute(self):
        """Test that len(name) returns the length of the name."""
        thorin = Name("Thorin")
        assert len(thorin) == 6

    def test_name_provides_access_to_syllables(self):
        """Test that name provides access to its syllables as Syllable objects."""
        thorin = Name("Thorin")

        assert thorin.syllables is not None
        assert isinstance(thorin.syllables, list)
        assert len(thorin.syllables) == 2

        for syllable in thorin.syllables:
            assert isinstance(syllable, Syllable)

    def test_complex_name_syllable_segmentation(self):
        """Test syllable segmentation for a complex name."""
        mephisto = Name("Mephistopheles")

        assert mephisto.syllables is not None
        assert isinstance(mephisto.syllables, list)
        assert len(mephisto.syllables) == 5

        for syllable in mephisto.syllables:
            assert isinstance(syllable, Syllable)

    def test_name_repr(self):
        """Test string representation of name."""
        name = Name("Test")
        expected = "Name('Test')"
        assert repr(name) == expected
