#!/usr/bin/env python3
"""
Corpus analysis tool for name generation.
"""

import argparse
import os
import sys
from collections import Counter
from typing import Dict

# Add the src directory to the path so we can import the package
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from wyrdbound_rng import FantasyNameSegmenter, Generator, JapaneseNameSegmenter
from wyrdbound_rng.name_list_resolver import format_available_lists


def analyze_corpus(generator: Generator, verbose: bool = False) -> Dict:
    """Analyze the loaded corpus."""
    analysis = {
        "total_names": len(generator.names),
        "unique_syllables": len(
            {str(s) for name in generator.names for s in name.syllables}
        ),
        "avg_syllables_per_name": sum(len(name.syllables) for name in generator.names)
        / len(generator.names),
        "syllable_frequency": Counter(),
    }

    # Count syllable frequencies
    for name in generator.names:
        for syllable in name.syllables:
            analysis["syllable_frequency"][str(syllable)] += 1

    # Convert to regular dict for JSON serialization
    analysis["syllable_frequency"] = dict(analysis["syllable_frequency"])

    if verbose:
        # Additional analysis
        name_lengths = [len(name.name) for name in generator.names]
        analysis["name_length_stats"] = {
            "min": min(name_lengths),
            "max": max(name_lengths),
            "avg": sum(name_lengths) / len(name_lengths),
        }

        syllable_counts = [len(name.syllables) for name in generator.names]
        analysis["syllable_count_stats"] = {
            "min": min(syllable_counts),
            "max": max(syllable_counts),
            "avg": sum(syllable_counts) / len(syllable_counts),
        }

    return analysis


def main():
    """Main function for the analysis tool."""
    parser = argparse.ArgumentParser(
        description="Analyze name corpus for generation patterns",
        prog="analyze",
        epilog=format_available_lists(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-l",
        "--list",
        required=True,
        help="Name list identifier (e.g., 'generic-fantasy') or path to YAML file",
    )
    parser.add_argument(
        "-s",
        "--segmenter",
        choices=["fantasy", "japanese"],
        default="fantasy",
        help="Segmentation method (default: fantasy)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed analysis"
    )
    parser.add_argument(
        "--top-syllables",
        type=int,
        default=20,
        help="Number of top syllables to show (default: 20)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    try:
        # Select segmenter
        if args.segmenter == "japanese":
            segmenter = JapaneseNameSegmenter()
        else:
            segmenter = FantasyNameSegmenter()

        # Create generator
        generator = Generator(args.list, segmenter=segmenter)

        # Analyze corpus
        analysis = analyze_corpus(generator, args.verbose)

        if args.json:
            import json

            print(json.dumps(analysis, indent=2))
        else:
            # Text output
            print(f"=== Corpus Analysis: {args.list} ===")
            print(f"Total names: {analysis['total_names']}")
            print(f"Unique syllables: {analysis['unique_syllables']}")
            print(
                f"Average syllables per name: {analysis['avg_syllables_per_name']:.2f}"
            )

            if args.verbose and "name_length_stats" in analysis:
                stats = analysis["name_length_stats"]
                print(
                    f"Name length: min={stats['min']}, max={stats['max']}, "
                    f"avg={stats['avg']:.2f}"
                )

                stats = analysis["syllable_count_stats"]
                print(
                    f"Syllable count: min={stats['min']}, max={stats['max']}, "
                    f"avg={stats['avg']:.2f}"
                )

            print(f"\nTop {args.top_syllables} syllables by frequency:")
            top_syllables = sorted(
                analysis["syllable_frequency"].items(), key=lambda x: x[1], reverse=True
            )[: args.top_syllables]

            for syllable, count in top_syllables:
                percentage = (
                    count / sum(analysis["syllable_frequency"].values())
                ) * 100
                print(f"  {syllable}: {count} ({percentage:.1f}%)")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
