"""Compare generated evidence packs with cross-platform numeric tolerance."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


REL_TOL = 1e-12
ABS_TOL = 1e-8


def _numbers_close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=REL_TOL, abs_tol=ABS_TOL)


def _compare_json(left: Any, right: Any, path: str = "root") -> list[str]:
    if isinstance(left, bool) or isinstance(right, bool):
        return [] if left == right else [f"{path}: {left!r} != {right!r}"]
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return [] if _numbers_close(float(left), float(right)) else [f"{path}: {left} != {right}"]
    if type(left) is not type(right):
        return [f"{path}: type {type(left).__name__} != {type(right).__name__}"]
    if isinstance(left, dict):
        differences: list[str] = []
        if left.keys() != right.keys():
            differences.append(f"{path}: keys differ")
        for key in left.keys() & right.keys():
            differences.extend(_compare_json(left[key], right[key], f"{path}.{key}"))
        return differences
    if isinstance(left, list):
        if len(left) != len(right):
            return [f"{path}: length {len(left)} != {len(right)}"]
        differences: list[str] = []
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            differences.extend(_compare_json(left_item, right_item, f"{path}[{index}]"))
        return differences
    return [] if left == right else [f"{path}: {left!r} != {right!r}"]


def _parse_number(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _compare_csv(reference: Path, generated: Path) -> list[str]:
    with reference.open(newline="", encoding="utf-8") as handle:
        left_rows = list(csv.reader(handle))
    with generated.open(newline="", encoding="utf-8") as handle:
        right_rows = list(csv.reader(handle))
    if len(left_rows) != len(right_rows):
        return [f"row count {len(left_rows)} != {len(right_rows)}"]
    differences: list[str] = []
    for row_index, (left_row, right_row) in enumerate(zip(left_rows, right_rows), start=1):
        if len(left_row) != len(right_row):
            differences.append(f"row {row_index}: column count differs")
            continue
        for column_index, (left, right) in enumerate(zip(left_row, right_row), start=1):
            left_number = _parse_number(left)
            right_number = _parse_number(right)
            if left_number is not None and right_number is not None:
                equal = _numbers_close(left_number, right_number)
            else:
                equal = left == right
            if not equal:
                differences.append(f"row {row_index}, column {column_index}: {left!r} != {right!r}")
            if len(differences) >= 20:
                return differences
    return differences


def compare_directories(reference_dir: Path, generated_dir: Path) -> list[str]:
    differences: list[str] = []
    evidence_files = sorted([*reference_dir.glob("*.json"), *reference_dir.glob("*.csv")])
    for reference in evidence_files:
        generated = generated_dir / reference.name
        if not generated.exists():
            differences.append(f"{reference.name}: generated file is missing")
            continue
        if reference.suffix == ".json":
            left = json.loads(reference.read_text(encoding="utf-8"))
            right = json.loads(generated.read_text(encoding="utf-8"))
            file_differences = _compare_json(left, right)
        else:
            file_differences = _compare_csv(reference, generated)
        differences.extend(f"{reference.name}: {item}" for item in file_differences)
    return differences


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference_dir", type=Path)
    parser.add_argument("generated_dir", type=Path)
    args = parser.parse_args()
    differences = compare_directories(args.reference_dir, args.generated_dir)
    if differences:
        print("Reproducibility check failed:")
        for difference in differences:
            print(f"- {difference}")
        raise SystemExit(1)
    print(f"Reproducibility check passed (rel_tol={REL_TOL:g}, abs_tol={ABS_TOL:g}).")


if __name__ == "__main__":
    main()
