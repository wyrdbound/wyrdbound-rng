#!/usr/bin/env python3
"""
Advanced name generation tool with analysis capabilities.
"""

import argparse
import json
import os
import sys

# Add the src directory to the path so we can import the package
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from wyrdbound_rng import FantasyNameSegmenter, Generator, JapaneseNameSegmenter
from wyrdbound_rng.name_list_resolver import format_available_lists


def main():
    """Main function for the advanced generation tool."""
    parser = argparse.ArgumentParser(
        description="Advanced name generation with analysis",
        prog="generate",
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
        "--count",
        type=int,
        default=1,
        help="Number of names to generate (default: 1)",
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
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed breakdown"
    )
    parser.add_argument(
        "--min-probability",
        type=float,
        default=1.0e-8,
        help="Minimum probability threshold for bayesian generation",
    )
    parser.add_argument(
        "--max-length", type=int, default=12, help="Maximum name length"
    )

    args = parser.parse_args()

    try:
        # Select segmenter
        if args.segmenter == "japanese":
            segmenter = JapaneseNameSegmenter()
        else:
            segmenter = FantasyNameSegmenter()

        # Create generator
        generator = Generator(args.list, segmenter=segmenter)

        # Generate names
        results = []
        for _i in range(args.count):
            name = generator.generate_name(
                max_len=args.max_length,
                algorithm=args.algorithm,
                min_probability_threshold=args.min_probability,
            )

            result = {"name": name.name, "algorithm": args.algorithm}

            if args.verbose:
                result["syllables"] = [str(s) for s in name.syllables]
                if hasattr(name, "source_names") and name.source_names:
                    result["source_names"] = name.source_names  # Already strings
                if hasattr(name, "probability") and name.probability:
                    result["probability"] = name.probability
                if hasattr(name, "exists_in_corpus"):
                    result["exists_in_corpus"] = name.exists_in_corpus

            if args.json:
                results.append(result)
            else:
                output = f"{result['name']}"
                if args.verbose:
                    if "syllables" in result:
                        output += f" (syllables: {' | '.join(result['syllables'])})"
                    if "source_names" in result:
                        output += f" (sources: {', '.join(result['source_names'])})"
                    if "probability" in result:
                        output += f" (probability: {result['probability']:.2e})"
                    if "exists_in_corpus" in result:
                        corpus_marker = (
                            "*exists in corpus*" if result["exists_in_corpus"] else ""
                        )
                        output += f" {corpus_marker}"
                print(output)

        if args.json:
            if len(results) == 1:
                print(json.dumps(results[0], indent=2))
            else:
                print(json.dumps(results, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
