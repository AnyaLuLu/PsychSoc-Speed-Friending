#!/usr/bin/env python3
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set, FrozenSet

from config_loader import load_config, read_participants_from_csv
from output_utils import write_round_to_markdown, print_round_to_console

# Re-use existing helpers from match.py
from match import (
    randomize_pairs,
)


# -----------------------------
# Data model
# -----------------------------

@dataclass
class Person:
    pid: str       # participant ID
    mbti: str      # MBTI type, e.g. "INTJ", "ENFP"


Pair = Tuple[Person, Person]
PastPairs = Set[FrozenSet[str]]  # frozenset of {id1, id2}


# -----------------------------
# MBTI similarity + pairing
# -----------------------------

def mbti_similarity(a: str, b: str) -> int:
    """
    Simple similarity score: how many letters are identical
    in the same position (0–4).
    """
    a = (a or "").upper().strip()
    b = (b or "").upper().strip()
    if len(a) != 4 or len(b) != 4:
        return 0

    score = 0
    for ca, cb in zip(a, b):
        if ca == cb:
            score += 1
    return score


def generate_candidate_pairs(
    people: List[Person],
    past_pairs: PastPairs,
) -> List[Tuple[int, Person, Person]]:
    """
    Generate all allowed (not previously used) pairs with
    their MBTI similarity scores.

    Returns a list of:
        (similarity_score, person_a, person_b)
    sorted from most similar to least.
    """
    candidates: List[Tuple[int, Person, Person]] = []
    n = len(people)

    for i in range(n):
        for j in range(i + 1, n):
            p1 = people[i]
            p2 = people[j]
            key = frozenset({p1.pid, p2.pid})
            if key in past_pairs:
                continue  # skip already-used pairs

            score = mbti_similarity(p1.mbti, p2.mbti)
            candidates.append((score, p1, p2))

    # Best matches first
    candidates.sort(key=lambda t: t[0], reverse=True)
    return candidates


def build_round(
    people: List[Person],
    past_pairs: PastPairs,
) -> Tuple[List[Pair], List[Person]]:
    """
    Build a single round of matches using MBTI similarity,
    without reusing any pair in past_pairs and without using
    any person more than once in this round.

    Returns:
        (pairs_for_this_round, leftover_people)
    """
    if len(people) < 2:
        return [], people[:]

    candidates = generate_candidate_pairs(people, past_pairs)

    used_ids: Set[str] = set()
    round_pairs: List[Pair] = []

    for score, p1, p2 in candidates:
        # If you want to forbid 0-similarity matches entirely, uncomment:
        # if score == 0:
        #     break

        if p1.pid in used_ids or p2.pid in used_ids:
            continue

        round_pairs.append((p1, p2))
        used_ids.add(p1.pid)
        used_ids.add(p2.pid)

    leftovers = [p for p in people if p.pid not in used_ids]
    return round_pairs, leftovers


def update_past_pairs(
    past_pairs: PastPairs,
    new_pairs: List[Pair],
) -> PastPairs:
    """
    Add newly-created pairs to the historical set.
    """
    updated = set(past_pairs)
    for p1, p2 in new_pairs:
        updated.add(frozenset({p1.pid, p2.pid}))
    return updated


# -----------------------------
# Round generator (MBTI-based)
# -----------------------------

def generate_rounds(
    scrambled_ids: List[str],
    num_rounds: int,
    participants: Dict[str, str],
) -> List[List[Tuple[str, str]]]:
    """
    MBTI-based version of generate_rounds.

    - scrambled_ids: list of participant IDs (already shuffled if desired).
    - num_rounds: how many rounds to generate.
    - participants: mapping id -> mbti (or id -> some string containing MBTI).

    Returns:
        List of rounds, where each round is a list of (id1, id2) tuples.

    Guarantees:
    - No pair (id1, id2) is repeated across rounds in this run.
    - Within a given round, each id appears at most once.
    """
    # Build Person list in the order of scrambled_ids
    people: List[Person] = [
        Person(pid=pid, mbti=str(participants.get(pid, "")).strip())
        for pid in scrambled_ids
    ]

    rounds: List[List[Tuple[str, str]]] = []
    past_pairs: PastPairs = set()

    for _ in range(num_rounds):
        pairs_this_round, _leftovers = build_round(people, past_pairs)

        # If no new pairs can be created without repeats, stop early.
        if not pairs_this_round:
            break

        # Convert Person pairs -> id pairs
        id_pairs = [(p1.pid, p2.pid) for (p1, p2) in pairs_this_round]
        rounds.append(id_pairs)

        # Update history
        past_pairs = update_past_pairs(past_pairs, pairs_this_round)

    return rounds


# -----------------------------
# Main entry point
# -----------------------------

def main() -> None:
    # Load config from YAML
    cfg = load_config()
    num_rounds = cfg["NUM_ROUNDS"]
    enable_random = cfg["ENABLE_RANDOM_TABLE_RANDOMIZATION"]
    random_seed = cfg["RANDOM_SEED"]
    csv_filename = cfg["CSV_FILENAME"]

    # Load participants from CSV
    # Assumption: participants is Dict[str, str] where value includes or is MBTI.
    participants: Dict[str, str] = read_participants_from_csv(csv_filename)
    ids = list(participants.keys())

    # Optional initial scrambling, same idea as match.py
    scrambled_ids = ids[:]
    if enable_random:
        random.seed(random_seed)
        random.shuffle(scrambled_ids)

    # Generate rounds using MBTI similarity & no repeated pairs
    rounds = generate_rounds(scrambled_ids, num_rounds, participants)

    print(f"Total participants: {len(ids)}")
    print(f"Generated {len(rounds)} rounds of pairings.\n")

    for r, pairs in enumerate(rounds, start=1):
        # Optional randomization of table order each round
        display_pairs = randomize_pairs(pairs, enable_random)

        # Console output
        print_round_to_console(r, display_pairs, participants)

        # Markdown output
        write_round_to_markdown(r, display_pairs, participants)


if __name__ == "__main__":
    main()
