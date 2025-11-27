# match.py

from typing import List, Tuple, Dict
import random

from config_loader import load_config, read_participants_from_csv
from output_utils import write_round_to_markdown, print_round_to_console


# =======================
# ROUND GENERATION
# =======================

def generate_rounds(ids: List[str], num_rounds: int) -> List[List[Tuple[str, str]]]:
    """
    Generate up to num_rounds of pairings using the round-robin (circle) method.
    Uses IDs rather than names; you can map to names later.

    Assumes len(ids) is even.

    - Total possible unique rounds = len(ids) - 1
    - We cap num_rounds at that maximum.
    """
    n = len(ids)
    if n < 2:
        return []

    max_rounds = n - 1
    if num_rounds > max_rounds:
        print(
            f"Requested {num_rounds} rounds, but maximum with {n} participants is {max_rounds}."
        )
        num_rounds = max_rounds

    players = list(ids)
    fixed = players[0]
    others = players[1:]  # length n-1

    rounds: List[List[Tuple[str, str]]] = []

    for _ in range(num_rounds):
        current = [fixed] + others

        pairs: List[Tuple[str, str]] = []
        for i in range(n // 2):
            p1 = current[i]
            p2 = current[n - 1 - i]
            pairs.append((p1, p2))

        rounds.append(pairs)

        # rotate others: move last element to front
        last = others[-1]
        others = [last] + others[:-1]

    return rounds


# =======================
# RANDOMIZATION HELPERS
# =======================

def randomize_pairs(
    pairs: List[Tuple[str, str]],
    enable: bool,
) -> List[Tuple[str, str]]:
    """
    Optionally return a randomized copy of the pair list.
    If enable is False, returns the pairs unchanged.
    """
    if not enable:
        return pairs
    shuffled = pairs[:]  # shallow copy
    random.shuffle(shuffled)
    return shuffled


def scramble_ids(ids: List[str]) -> List[str]:
    """
    Scramble the order of participant IDs before generating rounds.
    This ensures CSV order doesn't bias the pairing schedule.
    """
    shuffled = ids[:]  # shallow copy so we don't modify the original list
    random.shuffle(shuffled)
    return shuffled


# =======================
# MAIN
# =======================

def main():
    # Load config from YAML
    cfg = load_config()
    num_rounds = cfg["NUM_ROUNDS"]
    enable_random = cfg["ENABLE_RANDOM_TABLE_RANDOMIZATION"]
    random_seed = cfg["RANDOM_SEED"]
    csv_filename = cfg["CSV_FILENAME"]

    if random_seed is not None:
        random.seed(random_seed)

    # Load participants from CSV
    participants: Dict[str, str] = read_participants_from_csv(csv_filename)
    ids = list(participants.keys())

    # Scramble the IDs before generating any matchings
    scrambled_ids = scramble_ids(ids)

    # Generate unique pairs per round from scrambled order
    rounds = generate_rounds(scrambled_ids, num_rounds)

    print(f"Total participants: {len(ids)}")
    print(f"Generated {len(rounds)} rounds of pairings.\n")

    for r, pairs in enumerate(rounds, start=1):
        # Optional randomization of table order each round
        display_pairs = randomize_pairs(pairs, enable_random)

        # Console output
        print_round_to_console(r, display_pairs, participants)

        # Markdown output
        write_round_to_markdown(r, display_pairs, participants)

    print("Markdown files generated:")
    for r in range(1, len(rounds) + 1):
        print(f"  round_{r}.md")


if __name__ == "__main__":
    main()
