#!/usr/bin/env python3
"""
Command-line interface for the Wyrdbound Random Name Generator.
"""

import argparse
import sys

from .generator import Generator
from .name_list_resolver import format_available_lists
from .segmenters.fantasy_name_segmenter import FantasyNameSegmenter
from .segmenters.japanese_name_segmenter import JapaneseNameSegmenter


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Generate random names from a corpus",
        prog="wyrdbound-rng",
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
        "-n",
        "--number",
        type=int,
        default=5,
        help="Number of names to generate (default: 5)",
    )
    parser.add_argument(
        "--length", type=int, default=12, help="Maximum name length (default: 12)"
    )
    parser.add_argument(
        "-a",
        "--algorithm",
        choices=["very_simple", "simple", "bayesian"],
        default="simple",
        help="Generation algorithm (default: simple)",
    )
    parser.add_argument(
        "-s",
        "--segmenter",
        choices=["fantasy", "japanese"],
        default="fantasy",
        help="Segmentation method (default: fantasy)",
    )
    parser.add_argument(
        "--show-sources",
        action="store_true",
        help="Show source names used in generation",
    )
    parser.add_argument(
        "--show-analysis",
        action="store_true",
        help="Show analysis info: corpus existence for all algorithms, plus probability for bayesian algorithm",
    )
    parser.add_argument(
        "--min-probability",
        type=float,
        default=1.0e-8,
        help="Minimum probability threshold for bayesian generation (default: 1e-8)",
    )
    parser.add_argument(
        "--syllables",
        action="store_true",
        help="Show syllable breakdown for first few loaded names",
    )
    parser.add_argument(
        "--probabilities",
        type=str,
        metavar="SYLLABLE",
        help="Show probability information for a specific syllable (requires bayesian algorithm)",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.0.1")

    args = parser.parse_args()

    try:
        # Select segmenter
        if args.segmenter == "japanese":
            segmenter = JapaneseNameSegmenter()
        else:
            segmenter = FantasyNameSegmenter()

        # Create generator with the name list
        generator = Generator(args.list, segmenter=segmenter)

        if args.syllables:
            print("\n=== Syllable Breakdown (first 10 names) ===")
            for _i, name in enumerate(generator.names[:10]):
                print(f"{name.name}: {' | '.join([str(s) for s in name.syllables])}")
            print()

        if args.probabilities:
            if args.algorithm != "bayesian":
                print(
                    "Warning: Probability analysis works best with bayesian algorithm"
                )
            print(f"\n=== Probability Analysis for '{args.probabilities}' ===")

            # Split the input by commas to handle multiple syllables
            syllables = [s.strip() for s in args.probabilities.split(",")]

            for syllable in syllables:
                if len(syllables) > 1:
                    print(f"\n--- Analysis for '{syllable}' ---")

                # Get probability information for the syllable
                prob_info = generator.get_syllable_probability_info(syllable)

                if not prob_info:
                    print(
                        f"No probability information available for syllable '{syllable}'"
                    )
                    print("This could mean:")
                    print("- The syllable doesn't exist in the corpus")
                    print("- The Bayesian model hasn't been trained yet")
                else:
                    print(f"Syllable: {syllable}")
                    print(
                        f"Start probability: {prob_info.get('start_probability', 0.0):.4f}"
                    )
                    print(
                        f"End probability: {prob_info.get('end_probability', 0.0):.4f}"
                    )

                    print("\nTop transition probabilities:")
                    transitions_found = False
                    for i in range(1, 6):  # top_transition_1 through top_transition_5
                        transition_key = f"top_transition_{i}"
                        if transition_key in prob_info:
                            transitions_found = True
                            print(f"  {i}. {syllable} → {prob_info[transition_key]}")

                    if not transitions_found:
                        print("  No transition data available")

            print()

        # Generate names
        print(f"\n=== Generated Names ({args.algorithm} algorithm) ===")
        for i in range(args.number):
            name = generator.generate_name(
                max_len=args.length,
                algorithm=args.algorithm,
                min_probability_threshold=args.min_probability,
            )

            output = f"{i + 1}. {name.name}"

            if (
                args.show_sources
                and hasattr(name, "source_names")
                and name.source_names
            ):
                sources = name.source_names  # Already strings
                output += f" (sources: {', '.join(sources)})"

            if args.show_analysis:
                prob_info = []

                # Show probability if available (Bayesian algorithm)
                if hasattr(name, "probability") and name.probability is not None:
                    prob_info.append(f"probability: {name.probability:.2e}")

                # Always show corpus existence when --show-analysis is used
                exists_in_corpus = generator.name_exists_in_corpus(name.name)
                if exists_in_corpus:
                    prob_info.append("*exists in corpus*")
                else:
                    prob_info.append("new name")

                if prob_info:
                    output += f" ({', '.join(prob_info)})"

            print(output)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
