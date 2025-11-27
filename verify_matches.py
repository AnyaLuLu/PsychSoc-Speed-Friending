#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set, FrozenSet, Iterable


# -------------------------------------------------------------------
# CONFIG: adjust these patterns if needed
# -------------------------------------------------------------------

PAIR_LINE_PATTERNS = [
    # Markdown table row with 2 ID columns (with or without index)
    re.compile(
        r"^\s*\|\s*(?:\d+\s*\|\s*)?([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$"
    ),

    # Bullet line like "- alice & bob"
    re.compile(
        r"^\s*[-*]\s+([^\-&|]+?)\s*(?:&|-|vs|\|)\s*([^\-&|]+?)\s*$",
        re.IGNORECASE,
    ),

    # Fallback: "alice - bob"
    re.compile(
        r"^\s*([^\-|#]+?)\s*-\s*([^\-|#]+?)\s*$"
    ),
]


@dataclass(frozen=True)
class PairOccurrence:
    person1: str
    person2: str
    filename: str
    line_number: int
    line_text: str


# -------------------------------------------------------------------
# Parsing logic
# -------------------------------------------------------------------

def normalize_id(raw: str) -> str:
    return raw.strip()


def iter_pairs_in_file(path: str) -> Iterable[PairOccurrence]:
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            for pattern in PAIR_LINE_PATTERNS:
                m = pattern.match(stripped)
                if not m:
                    continue

                raw1, raw2 = m.group(1), m.group(2)
                id1 = normalize_id(raw1)
                id2 = normalize_id(raw2)

                if not id1 or not id2:
                    continue

                yield PairOccurrence(
                    person1=id1,
                    person2=id2,
                    filename=os.path.basename(path),
                    line_number=lineno,
                    line_text=stripped,
                )
                break


def collect_pairs(root_dir: str, pattern: str = ".md") -> Dict[FrozenSet[str], List[PairOccurrence]]:
    all_pairs: Dict[FrozenSet[str], List[PairOccurrence]] = {}

    for dirpath, _dirnames, filenames in os.walk(root_dir):
        for name in filenames:
            # -------------------------------
            # NEW RULE: Skip LICENSE.md
            # -------------------------------
            if name.lower() == "license.md":
                continue

            if not name.endswith(pattern):
                continue

            full_path = os.path.join(dirpath, name)
            for occ in iter_pairs_in_file(full_path):
                key = frozenset({occ.person1, occ.person2})
                all_pairs.setdefault(key, []).append(occ)

    return all_pairs


# -------------------------------------------------------------------
# Duplicate detection
# -------------------------------------------------------------------

def find_duplicates(all_pairs: Dict[FrozenSet[str], List[PairOccurrence]]) -> Dict[FrozenSet[str], List[PairOccurrence]]:
    return {k: v for k, v in all_pairs.items() if len(v) > 1}


def print_report(
    duplicates: Dict[FrozenSet[str], List[PairOccurrence]],
    verbose: bool = True,
) -> None:
    if not duplicates:
        print("✅ No duplicate matches found across markdown files.")
        return

    print("❌ Duplicate matches detected!\n")

    for pair_key, occs in sorted(
        duplicates.items(),
        key=lambda kv: sorted(list(kv[0]))
    ):
        ids = sorted(list(pair_key))
        print(f"Pair: {ids[0]}  ↔  {ids[1]}  (seen {len(occs)} times)")
        if verbose:
            for occ in occs:
                print(
                    f"  - {occ.filename}: line {occ.line_number}: {occ.line_text}"
                )
        print()


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------

def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that no participant pair appears more than once "
            "across markdown match files."
        )
    )
    parser.add_argument(
        "root",
        help="Root directory containing match .md files."
    )
    parser.add_argument(
        "--ext",
        default=".md",
        help="Markdown file extension (default: .md)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output (suitable for CI)."
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    root_dir = os.path.abspath(args.root)
    if not os.path.isdir(root_dir):
        print(f"Error: '{root_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    all_pairs = collect_pairs(root_dir, pattern=args.ext)
    duplicates = find_duplicates(all_pairs)

    print_report(duplicates, verbose=not args.quiet)

    sys.exit(1 if duplicates else 0)


if __name__ == "__main__":
    main()
