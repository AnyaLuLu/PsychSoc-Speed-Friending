# match.py

from typing import List, Tuple, Dict
from pathlib import Path
import random

from config_loader import load_config, read_participants_from_csv


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
# OUTPUT (MARKDOWN + CONSOLE)
# =======================

def write_round_to_markdown(
    round_index: int,
    pairs: List[Tuple[str, str]],
    participants: Dict[str, str],
):
    """
    Write one round of pairings to a Markdown file named round_<n>.md.
    If the file exists, it is overwritten.

    pairs are (id1, id2), participants maps id -> name
    """
    filename = Path(f"round_{round_index}.md")
    if filename.exists():
        filename.unlink()

    lines = []
    lines.append(f"# Round {round_index}\n")
    lines.append("| Table # | Name 1 | Name 2 |")
    lines.append("|--------:|--------|--------|")

    for table_num, (id1, id2) in enumerate(pairs, start=1):
        name1 = participants[id1].replace("|", "\\|")
        name2 = participants[id2].replace("|", "\\|")
        lines.append(f"| {table_num} | {name1} | {name2} |")

    content = "\n".join(lines) + "\n"
    filename.write_text(content, encoding="utf-8")


def print_round_to_console(
    round_index: int,
    pairs: List[Tuple[str, str]],
    participants: Dict[str, str],
):
    """
    Pretty-print one round to the console in a table format.
    """
    print(f"Round {round_index}:")
    print("-" * 60)
    print(f"{'Table #':<8} {'Name 1':<24} {'Name 2':<24}")
    print("-" * 60)

    for table_num, (id1, id2) in enumerate(pairs, start=1):
        name1 = participants[id1]
        name2 = participants[id2]
        print(f"{table_num:<8} {name1:<24} {name2:<24}")

    print()  # blank line between rounds


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
    participants = read_participants_from_csv(csv_filename)
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
