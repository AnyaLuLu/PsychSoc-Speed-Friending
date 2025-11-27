# output_utils.py

from typing import Dict, List, Tuple
from pathlib import Path


def write_round_to_markdown(
    round_index: int,
    pairs: List[Tuple[str, str]],
    participants: Dict[str, str],
) -> None:
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
) -> None:
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
