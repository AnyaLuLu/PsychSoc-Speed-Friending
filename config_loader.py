# config_loader.py

from typing import Dict
import csv
import yaml


def load_config(path: str = "config.yaml") -> Dict:
    """Load configuration values from a YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    return {
        "NUM_ROUNDS": cfg.get("num_rounds", 5),
        "ENABLE_RANDOM_TABLE_RANDOMIZATION": cfg.get("enable_random_table_randomization", True),
        "RANDOM_SEED": cfg.get("random_seed", None),
        "CSV_FILENAME": cfg.get("csv_filename", "names.csv"),
    }


def read_participants_from_csv(filename: str) -> Dict[str, str]:
    """
    Read participants from a CSV file.

    Expected columns (header row, case-insensitive):
        - id
        - name

    Extra columns (like MBTI) are ignored.

    Returns:
        dict: { id_str: name_str }

    Raises:
        ValueError if no rows or odd number of participants.
    """
    participants: Dict[str, str] = {}

    with open(filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames:
            raise ValueError(f"{filename} has no header row.")

        # normalize headers to lower-case
        field_map = {name.lower(): name for name in reader.fieldnames}

        required = ["id", "name"]
        missing = [col for col in required if col not in field_map]
        if missing:
            raise ValueError(
                f"CSV file must contain columns: {required}, missing: {missing}"
            )

        for row in reader:
            pid = row[field_map["id"]].strip()
            name = row[field_map["name"]].strip()

            if not pid or not name:
                continue  # skip incomplete rows

            participants[pid] = name

    if not participants:
        raise ValueError(f"{filename} contains no valid participants.")

    if len(participants) % 2 != 0:
        raise ValueError(
            f"Number of participants must be even, got {len(participants)}."
        )

    return participants
