from wyrdbound_rng.segmenters.japanese_name_segmenter import JapaneseNameSegmenter


class TestJapaneseNameSegmenter:
    """Test suite for JapaneseNameSegmenter, ported from Ruby specs."""

    def test_segment_single_syllable_names(self):
        """Test segmenting single syllable names."""
        single_syllable_names = ["Go", "Ya", "Fu"]

        for name in single_syllable_names:
            syllables = JapaneseNameSegmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)
            assert len(syllables) == 1

    def test_segment_double_syllable_names(self):
        """Test segmenting double syllable names."""
        # Updated to reflect improved Japanese segmentation
        # "Bun" is correctly segmented as 1 syllable (CVC with final 'n')
        double_syllable_names = ["Boze", "Kazu", "Fumi", "Saji"]
        single_syllable_names = ["Bun"]  # CVC pattern with final 'n'

        for name in double_syllable_names:
            syllables = JapaneseNameSegmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)
            assert len(syllables) == 2, (
                f"{name} should be 2 syllables, got {len(syllables)}: {[str(s) for s in syllables]}"
            )

        for name in single_syllable_names:
            syllables = JapaneseNameSegmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)
            assert len(syllables) == 1, (
                f"{name} should be 1 syllable, got {len(syllables)}: {[str(s) for s in syllables]}"
            )

    def test_segment_triple_syllable_names(self):
        """Test segmenting triple syllable names."""
        triple_syllable_names = ["Asano", "Kaiga", "Hoizu", "Mikami", "Fudajo"]

        for name in triple_syllable_names:
            syllables = JapaneseNameSegmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)
            assert len(syllables) == 3

    def test_segment_quadruple_syllable_names(self):
        """Test segmenting quadruple syllable names."""
        # Updated to reflect improved Japanese segmentation with gemination
        quadruple_syllable_names = ["Nobunaga", "Ieyasu", "Masamune", "Ujiie"]
        three_syllable_names = [
            "Bungoro",
            "Hattori",
            "Echizen",
        ]  # Gemination and improved segmentation

        for name in quadruple_syllable_names:
            syllables = JapaneseNameSegmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)
            assert len(syllables) == 4, (
                f"{name} should be 4 syllables, got {len(syllables)}: {[str(s) for s in syllables]}"
            )

        for name in three_syllable_names:
            syllables = JapaneseNameSegmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)
            assert len(syllables) == 3, (
                f"{name} should be 3 syllables, got {len(syllables)}: {[str(s) for s in syllables]}"
            )

    def test_segment_long_names(self):
        """Test segmenting very long names."""
        # Updated to reflect improved Japanese segmentation
        long_names = [
            "Chousokabe",
            "Shikanosuke",
            "Kirigakure",
        ]  # These are 5 syllables
        medium_names = ["Honganji"]  # This is 3 syllables

        for name in long_names:
            syllables = JapaneseNameSegmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)
            assert len(syllables) >= 5, (
                f"{name} should be >=5 syllables, got {len(syllables)}: {[str(s) for s in syllables]}"
            )

        for name in medium_names:
            syllables = JapaneseNameSegmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)
            assert len(syllables) == 3, (
                f"{name} should be 3 syllables, got {len(syllables)}: {[str(s) for s in syllables]}"
            )

    def test_segment_non_overlapping_non_empty_syllables(self):
        """Test that segmentation produces non-overlapping, non-empty syllables."""
        test_names = ["Hanzou", "Kotarou", "Fuuma"]

        for name in test_names:
            syllables = JapaneseNameSegmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)

            # Verify syllables join back to original name (lowercased)
            joined = "".join(str(syl) for syl in syllables)
            assert joined == name.lower()

    def test_segment_doubled_n_as_in_geni(self):
        """Test segmenting doubled n's as in Gen'i."""
        # Updated to reflect improved Japanese segmentation
        # Gen'i is correctly segmented as 2 syllables: gen + 'i
        syllables = JapaneseNameSegmenter.segment("Gen'i")
        assert syllables is not None
        assert isinstance(syllables, list)
        assert len(syllables) == 2, (
            f"Gen'i should be 2 syllables, got {len(syllables)}: {[str(s) for s in syllables]}"
        )
        assert str(syllables[0]) == "gen"
        assert str(syllables[1]) == "'i"
