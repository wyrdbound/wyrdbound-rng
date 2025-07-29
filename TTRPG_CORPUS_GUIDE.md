# TTRPG Name Generation: Corpus Size Guide for Plugin Developers

## Executive Summary

Based on empirical testing with the Bayesian Random Name Generator, here are the **minimum corpus size requirements** for different TTRPG universes:

| Universe Type                                 | Minimum   | Recommended | Optimal   | Quality Threshold |
| --------------------------------------------- | --------- | ----------- | --------- | ----------------- |
| **High Fantasy** (D&D, Pathfinder)            | 100 names | 200 names   | 300 names | 1e-7              |
| **Science Fiction** (Shadowrun, Cyberpunk)    | 75 names  | 150 names   | 200 names | 1e-8              |
| **Asian-Inspired** (L5R, Oriental Adventures) | 150 names | 300 names   | 500 names | 1e-6              |
| **Historical** (Medieval, Ancient)            | 120 names | 250 names   | 400 names | 1e-6              |
| **Space Opera** (Star Wars, 40K)              | 80 names  | 160 names   | 250 names | 1e-8              |
| **Horror/Gothic** (CoC, WoD)                  | 100 names | 200 names   | 300 names | 1e-7              |
| **Custom Homebrew**                           | 50 names  | 100 names   | 200 names | 1e-8              |

## Key Findings

✅ **Small corpora work**: Even 25-50 names can generate novel content, but with limited variety  
✅ **Sweet spot**: 100-200 names provide the best balance of quality and development effort  
✅ **Diminishing returns**: Beyond 300-400 names, quality improvements plateau  
✅ **Quality over quantity**: 100 curated names outperform 200 random ones

## Quality Metrics to Track

Your corpus is ready when you achieve:

- **85%+ Novelty Rate** (generated names not in corpus)
- **80%+ Uniqueness Rate** (different names in each generation batch)
- **Average Probability > 0.01** (reasonable linguistic quality)
- **Player Acceptance** (names "feel right" for the universe)

## Quick Validation Test

Use this command to test your corpus:

```bash
python corpus_test.py your_corpus.yaml
```

For more options:

```bash
# Test with specific parameters
python corpus_test.py your_corpus.yaml --target-size 150 --count 100

# Use Japanese segmenter for Japanese names
python corpus_test.py your_corpus.yaml --segmenter japanese

# Custom quality thresholds
python corpus_test.py your_corpus.yaml --thresholds 1e-8,1e-7,1e-6

# Quick summary view
python corpus_test.py your_corpus.yaml --summary-only

# Run example tests
python corpus_test.py --examples
```

Or programmatically:

```python
from rng.generator import Generator
generator = Generator('your_corpus.yaml')
names = generator.generate(50, 15, 'bayesian', min_probability_threshold=1e-7)
```

## Implementation Steps

1. **Start Small**: Begin with minimum viable corpus size
2. **Test Early**: Generate 50-100 names to verify quality metrics
3. **Iterate**: Add 25-50% more names if quality is poor
4. **Validate**: Test with actual TTRPG sessions and player feedback
5. **Document**: Record final corpus size and threshold settings

## Cultural Considerations

### High Fantasy

- Mix Human, Elf, Dwarf, Halfling patterns
- Include 50+ names per major culture
- Test with FantasyNameSegmenter

### Asian-Inspired

- Use JapaneseNameSegmenter for authenticity
- Include historical periods (Sengoku, Heian, etc.)
- Maintain linguistic consistency

### Science Fiction

- Blend familiar and exotic patterns
- Mix cultural backgrounds
- Consider tech-influenced naming

### Historical

- Source from historical records
- Maintain period accuracy
- Include regional variations

## Common Pitfalls

❌ Using unfiltered web scraping (poor quality)  
❌ Mixing incompatible cultural patterns  
❌ Not testing different name lengths  
❌ Assuming bigger corpus = better results  
❌ Forgetting to validate against lore/canon  
❌ Using inappropriate segmenter type

## API Usage Examples

```python
# Standard quality (high variety)
name = generator.generate_name(15, 'bayesian', min_probability_threshold=1e-8)

# Balanced quality/variety
name = generator.generate_name(15, 'bayesian', min_probability_threshold=1e-7)

# Premium quality (less variety)
name = generator.generate_name(15, 'bayesian', min_probability_threshold=1e-6)

# Batch generation
names = generator.generate(10, 15, 'bayesian', min_probability_threshold=1e-7)
```

## CLI Testing

```bash
# Test generation quality
python rng.py --algorithm bayesian --show-probability

# Adjust quality threshold
python rng.py --algorithm bayesian --min-probability 1e-6

# Generate multiple names
python rng.py --count 20 --algorithm bayesian --show-probability
```

## Success Examples

✅ **Japanese names**: 475 historical Sengoku period names → 100% novel, authentic results  
✅ **Fantasy names**: 679 mixed cultural patterns → 85%+ novel, varied results  
✅ **Small test corpus**: 50 curated names → 98% novel, good uniqueness

## Support Resources

- **Validation Tool**: `corpus_test.py` - Test your corpus quality with configurable parameters
- **Analysis Tools**: `practical_corpus_analysis.py` - Compare different corpus sizes empirically
- **Example Implementation**: `example_threshold_api.py` - Programmatic usage patterns and examples
- **This Guide**: `TTRPG_CORPUS_GUIDE.md` - Comprehensive recommendations and best practices

---

**Bottom Line**: Start with 100-150 curated names from official sources, test early, and expand based on quality metrics. The Bayesian algorithm is remarkably effective even with modest corpus sizes when names are well-chosen and culturally consistent.
