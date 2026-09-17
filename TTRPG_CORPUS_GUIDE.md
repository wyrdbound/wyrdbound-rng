# TTRPG Name Generation: Corpus Size Guide for Plugin Developers

## Executive Summary

This guide is a **rule of thumb**, not a measurement. The size figures below are
experience-based starting points for corpus authors; the numbers that decide
whether a corpus is finished are measured by `tools/corpus_test.py`, and the
reasoning behind them is in `CORPUS_REPORT.md`. Where the two disagree, the
measured tool wins.

| Universe Type                                 | Rough starting size | Quality Threshold |
| --------------------------------------------- | ------------------- | ----------------- |
| **High Fantasy** (D&D, Pathfinder)            | 200-300 names       | 1e-7              |
| **Science Fiction** (Shadowrun, Cyberpunk)    | 150-200 names       | 1e-8              |
| **Asian-Inspired** (L5R, Oriental Adventures) | 300-500 names       | 1e-6              |
| **Historical** (Medieval, Ancient)            | 250-400 names       | 1e-6              |
| **Space Opera** (Star Wars, 40K)              | 160-250 names       | 1e-8              |
| **Horror/Gothic** (CoC, WoD)                  | 200-300 names       | 1e-7              |
| **Custom Homebrew**                           | 100-200 names       | 1e-8              |

## Key Findings

- **Small corpora work**: even 25-50 names can generate novel content, but with
  limited variety and a real risk of the generator regurgitating them.
- **Coherence beats count**: 100 names that share one sound system train a
  better model than 679 names that each introduce a brand-new syllable. Measure
  syllable-pair coverage, not name count.
- **Diminishing returns**: coverage climbs steeply to roughly 400 names for a
  coherent list and then flattens. See `CORPUS_REPORT.md` §4 for the measured
  curves.
- **Quality over quantity**: 100 curated names outperform 200 random ones.

## Quality Metrics to Track

Track coverage, not novelty. `tools/corpus_test.py` reports:

- **Unigram coverage ≥ 0.93** (Good-Turing: probability the next name adds no
  new syllable)
- **Bigram coverage ≥ 0.64** (the same for ordered syllable pairs, which is what
  the Bayesian model actually learns from)
- **Uniqueness ≥ 0.85** (distinct names within a generation batch — this is what
  stops a name recurring in one session)
- **Novelty ≥ 0.60** (generated names not already in the corpus — a floor to
  catch a corpus so small the generator can only repeat it)

### Do not chase a high novelty rate

An earlier version of this guide asked for **85%+ novelty**. That target is
actively harmful, and it is worth understanding why. Novelty and name quality
trade off inversely: the high-probability syllable transitions that produce
plausible names are the same ones the corpus already exhausted on real names.

Measured on one corpus at one length cap:

```
simple      95% novel   Warwaaibald, Gugomarger, Lameramfred, Foethelm
bayesian    69% novel   Guilhard, Adalward, Lambert, Engelwig, Bertgleif
```

Chasing 85% selects the top row. The bottom row is the one you want.
`tools/corpus_test.py` sets its novelty bar at 60% for exactly this reason.

## Quick Validation Test

`tools/corpus_test.py` is the committed measurement tool:

```bash
# Full report for one corpus
python tools/corpus_test.py --list ancestry-dwarf-male

# Ranked sweep over every built-in list
python tools/corpus_test.py --all

# Machine-readable output
python tools/corpus_test.py --list ancestry-dwarf-male --json

# Use the Japanese segmenter
python tools/corpus_test.py --list japanese-sengoku -s japanese
```

Programmatically:

```python
from wyrdbound_rng import Generator

generator = Generator("ancestry-dwarf-male")
names = generator.generate(50, 15, "bayesian", min_probability_threshold=1e-7)
```

## Implementation Steps

1. **Start with a coherent set**: gather names that share one sound system.
2. **Test early**: run `tools/corpus_test.py` and read the coverage figures.
3. **Iterate on coherence, not volume**: add variety within the style, not more
   names of the same kind, if coverage has stalled.
4. **Validate**: test with actual TTRPG sessions and player feedback.
5. **Document**: record the final corpus size and threshold settings.

## Cultural Considerations

### High Fantasy

- Keep ancestry registers separate rather than mixing them; the built-in
  `ancestry-*` lists are the worked example.
- Test with `FantasyNameSegmenter`.

### Asian-Inspired

- Use `JapaneseNameSegmenter` for authenticity.
- Maintain linguistic consistency within a corpus.

### Science Fiction

- Blend familiar and exotic patterns deliberately.
- Mix cultural backgrounds, but keep each corpus internally coherent.

### Historical

- Source from historical records.
- Maintain period accuracy and regional variation.

## Common Pitfalls

- Using unfiltered web scraping (poor quality).
- Mixing incompatible cultural patterns in one corpus.
- Not testing different name lengths.
- Assuming a bigger corpus is a better one. It is not: `generic-fantasy` has 679
  names and 685 distinct syllables, so there is nothing for the model to learn.
- Forgetting to validate against lore/canon.
- Using the wrong segmenter type.

## API Usage Examples

```python
# Standard quality (high variety)
name = generator.generate_name(15, "bayesian", min_probability_threshold=1e-8)

# Balanced quality/variety
name = generator.generate_name(15, "bayesian", min_probability_threshold=1e-7)

# Premium quality (less variety)
name = generator.generate_name(15, "bayesian", min_probability_threshold=1e-6)

# Batch generation
names = generator.generate(10, 15, "bayesian", min_probability_threshold=1e-7)
```

## CLI Testing

```bash
# Test generation quality
wyrdbound-rng -l generic-fantasy -a bayesian --show-analysis

# Adjust quality threshold
wyrdbound-rng -l generic-fantasy -a bayesian --min-probability 1e-6

# Generate multiple names
wyrdbound-rng -l generic-fantasy -n 20 -a bayesian --show-analysis
```

## Success Examples

The coherence finding, from `CORPUS_REPORT.md` §1. Both corpora produce novel
names; only one trains a model:

```
japanese-sengoku-samurai   384 names   84 unique syllables   0.986 unigram   0.822 bigram
generic-fantasy            679 names  685 unique syllables   0.756 unigram   0.423 bigram
```

`generic-fantasy`'s 685 syllables across 679 names means roughly one brand-new
syllable per name, so no transition probability is ever established — the
generator can only collage it. A coherent corpus reaches higher coverage on half
the names because its syllables each recur often enough to learn from.

## Support Resources

- **Measurement Tool**: `tools/corpus_test.py` — corpus coverage, saturation and
  sizing, with JSON output.
- **Corpus Builder**: `tools/build_corpora.py` — the ten built-in ancestry
  corpora, rebuilt deterministically from name-element stock.
- **Measurement Report**: `CORPUS_REPORT.md` — method and findings.
- **This Guide**: `TTRPG_CORPUS_GUIDE.md` — rules of thumb and best practices.

---

**Bottom Line**: Pick a coherent set of names and measure its syllable coverage.
Name count is a weak proxy for quality; the size figures here are rules of thumb
and `tools/corpus_test.py` is the arbiter.
