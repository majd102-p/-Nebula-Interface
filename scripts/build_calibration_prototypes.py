import csv
import json
from collections import defaultdict
from pathlib import Path

CSV_PATH = Path("configs/calibration_samples.csv")
JSON_PATH = Path("configs/calibration_prototypes.json")


def _mean_vector(vectors):
    if not vectors:
        return []

    length = len(vectors[0])
    totals = [0.0] * length
    for vector in vectors:
        for index, value in enumerate(vector):
            totals[index] += value

    count = float(len(vectors))
    return [round(value / count, 6) for value in totals]


def build_prototypes(csv_path=CSV_PATH, json_path=JSON_PATH):
    if not csv_path.exists():
        raise FileNotFoundError(f"Calibration CSV not found: {csv_path}")

    grouped = defaultdict(list)

    with open(csv_path, "r", encoding="utf-8", newline="") as file_handle:
        reader = csv.reader(file_handle)
        for row in reader:
            if len(row) < 8:
                continue

            label = row[0].strip()
            if not label:
                continue

            try:
                vector = [float(value) for value in row[7:]]
            except ValueError:
                continue

            grouped[label].append(vector)

    if not grouped:
        raise ValueError("No usable calibration samples found")

    payload = {
        "version": 1,
        "source": str(csv_path),
        "labels": {},
    }

    for label, vectors in grouped.items():
        payload["labels"][label] = {
            "sample_count": len(vectors),
            "vector_length": len(vectors[0]),
            "prototype": _mean_vector(vectors),
        }

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2)

    return json_path


if __name__ == "__main__":
    output = build_prototypes()
    print(f"Saved calibration prototypes to {output}")
