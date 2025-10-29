"""Utility script to inspect fuzzy slug search results.

Run this module directly to print search results for a collection of
queries. Useful for diagnosing cases where fuzzy matching feels
overly broad or matches on character patterns instead of relevance.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

from grokipedia_sdk.slug_index import SlugIndex

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - optional dependency
    fuzz = None  # type: ignore


DEFAULT_QUERIES: List[str] = [
    "ai",
    "joe bidan",
    "artificial inteligence",
    "open ai",
    "large language model",
    "tesla autopilot",
    "spark plug",
    "mars mission",
    "machine learnin",
    "global warmin",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect substring vs fuzzy slug search results",
    )
    parser.add_argument(
        "queries",
        nargs="*",
        help="Queries to test; defaults to an internal list when omitted",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results to display per query (default: 10)",
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.6,
        help="Minimum similarity threshold passed to SlugIndex.search",
    )
    parser.add_argument(
        "--links-dir",
        type=Path,
        default=None,
        help="Optional path to the Grokipedia links directory",
    )
    parser.add_argument(
        "--use-bktree",
        action="store_true",
        help="Force-enable BK-tree construction (disabled if rapidfuzz missing)",
    )
    return parser.parse_args()


def _format_score(value: float) -> str:
    return f"{int(round(value)):3d}"


def compute_similarity_strings(query: str, slug: str) -> str:
    if not fuzz:
        return ""

    query_norm = SlugIndex._normalize_name(query)
    slug_norm = SlugIndex._normalize_name(slug)

    ratio = fuzz.ratio(query_norm, slug_norm)

    details = [f"ratio={_format_score(ratio)}"]

    # Token based ratios provide a better sense of word-level similarity.
    try:
        token_ratio = fuzz.token_set_ratio(query_norm, slug_norm)
        details.append(f"token_set={_format_score(token_ratio)}")
    except AttributeError:
        pass

    try:
        wratio = fuzz.WRatio(query_norm, slug_norm)
        details.append(f"wratio={_format_score(wratio)}")
    except AttributeError:
        pass

    return " (" + ", ".join(details) + ")"


def render_results(header: str, slugs: Iterable[str], query: str) -> None:
    slugs = list(slugs)
    print(f"  {header} ({len(slugs)} results)")
    if not slugs:
        print("    (none)")
        return

    for idx, slug in enumerate(slugs, start=1):
        similarity = compute_similarity_strings(query, slug)
        print(f"    {idx:2d}. {slug}{similarity}")


def inspect_queries(index: SlugIndex, queries: Iterable[str], limit: int, min_similarity: float) -> None:
    for query in queries:
        print("=" * 80)
        print(f"Query: {query!r}\n")

        substring_matches = index.search(query, limit=limit, fuzzy=False)
        render_results("Substring", substring_matches, query)

        fuzzy_matches = index.search(query, limit=limit, fuzzy=True, min_similarity=min_similarity)
        render_results("Fuzzy", fuzzy_matches, query)

        substring_set = set(substring_matches)
        fuzzy_only = [slug for slug in fuzzy_matches if slug not in substring_set]

        if fuzzy_only:
            render_results("Fuzzy (no substring overlap)", fuzzy_only, query)

        best_match = index.find_best_match(query, min_similarity=min_similarity)
        if best_match:
            similarity = compute_similarity_strings(query, best_match)
            print(f"\n  Best match: {best_match}{similarity}")
        else:
            print("\n  Best match: None")

        print()


def main() -> None:
    args = parse_args()
    queries = args.queries or DEFAULT_QUERIES

    index = SlugIndex(links_dir=args.links_dir, use_bktree=args.use_bktree)
    index.load()

    print(f"Loaded {index.get_total_count():,} slugs\n")
    print(f"Using min_similarity={args.min_similarity} and limit={args.limit}\n")

    inspect_queries(index, queries, limit=args.limit, min_similarity=args.min_similarity)


if __name__ == "__main__":
    main()

