from typing import List, Tuple
from pathlib import Path
import csv

def read_names(filename: str = "names.txt") -> List[str]:
    """Read one name per line from filename. Ignores empty lines."""
    with open(filename, "r", encoding="utf-8") as f:
        names = [line.strip() for line in f if line.strip()]
    if len(names) == 0:
        raise ValueError("names.txt is empty.")
    if len(names) % 2 != 0:
        raise ValueError(f"Number of names must be even, got {len(names)}.")
    return names

# takes in a csv file with name, id, and MBTI columns
# outputs dict of id to (name, MBTI)
def read_names_from_csv(filename: str = "names.csv") -> dict:
    """Read names, ids, and MBTI types from a CSV file."""
    data = {}
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name'].strip()
            id = row['id'].strip()
            mbti = row['MBTI'].strip()
            if name and id:
                data[id] = (name, mbti)
    if len(data) == 0:
        raise ValueError("CSV file is empty or improperly formatted.")
    if len(data) % 2 != 0:
        raise ValueError(f"Number of entries must be even, got {len(data)}.")
    return data

def mbti_similarity(a: str, b: str) -> int:
    """Return similarity score between two MBTI types (0–4)."""
    if len(a) != 4 or len(b) != 4:
        return 0
    return sum(1 for x, y in zip(a.upper(), b.upper()) if x == y)


def generate_rounds(names: List[str], num_rounds: int) -> List[List[Tuple[str, str]]]:
    """
    Generate up to num_rounds of pairings using the round-robin (circle) method.
    Assumes len(names) is even.

    - Total possible unique rounds = len(names) - 1
    - We cap num_rounds at that maximum.
    """
    n = len(names)
    if n < 2:
        return []

    max_rounds = n - 1
    if num_rounds > max_rounds:
        print(f"Requested {num_rounds} rounds, but maximum with {n} names is {max_rounds}.")
        num_rounds = max_rounds

    players = list(names)
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

def write_round_to_markdown(round_index: int, pairs: List[Tuple[str, str]]):
    """
    Write one round of pairings to a Markdown file named round_<n>.md.
    If the file exists, it is overwritten.
    """
    filename = Path(f"round_{round_index}.md")
    # Delete first if it exists (not strictly necessary since we'll overwrite,
    # but matches your request to delete if present).
    if filename.exists():
        filename.unlink()

    lines = []
    lines.append(f"# Round {round_index}\n")
    lines.append("| Table # | Name 1 | Name 2 |")
    lines.append("|--------:|--------|--------|")

    for table_num, (a, b) in enumerate(pairs, start=1):
        # Escape pipe characters if they appear in names
        a_escaped = a.replace("|", "\\|")
        b_escaped = b.replace("|", "\\|")
        lines.append(f"| {table_num} | {a_escaped} | {b_escaped} |")

    content = "\n".join(lines) + "\n"
    filename.write_text(content, encoding="utf-8")

def main():
    names = read_names("names.txt")
    data = read_names_from_csv("names.csv")

    # Set how many rounds you want:
    num_rounds = 5

    rounds = generate_rounds(names, num_rounds=num_rounds)

    print(f"Total names: {len(names)}")
    print(f"Generated {len(rounds)} rounds of pairings.\n")

    for r, pairs in enumerate(rounds, start=1):
        # Console output
        print(f"Round {r}:")
        print("-" * 40)
        print(f"{'Table #':<8} {'Name 1':<20} {'Name 2':<20}")
        print("-" * 40)

        for table_num, (a, b) in enumerate(pairs, start=1):
            print(f"{table_num:<8} {a:<20} {b:<20}")
        print()  # blank line between rounds

        # Markdown output
        write_round_to_markdown(r, pairs)

    print("Markdown files generated:")
    for r in range(1, len(rounds) + 1):
        print(f"  round_{r}.md")
    print(data)



if __name__ == "__main__":
    main()
