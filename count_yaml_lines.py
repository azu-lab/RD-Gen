#!/usr/bin/env python3
import argparse
from pathlib import Path

def count_non_empty_lines(file_path: Path) -> int:
    count = 0
    with file_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count

def iter_yaml_files(root_dir: Path):
    for path in root_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}:
            yield path

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute total and average line counts for YAML files under a directory."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="test",
        help="Directory to scan (default: test)",
    )
    parser.add_argument(
        "--min-lines",
        type=int,
        default=10,
        help="Ignore files with fewer non-empty lines than this (default: 10)",
    )
    args = parser.parse_args()

    root_dir = Path(args.directory)
    if not root_dir.exists():
        print(f"Directory not found: {root_dir}")
        return 1

    total_lines = 0
    file_count = 0

    for yaml_file in iter_yaml_files(root_dir):
        line_count = count_non_empty_lines(yaml_file)
        if line_count < args.min_lines:
            continue
        total_lines += line_count
        file_count += 1

    if file_count == 0:
        print("No YAML files found.")
        return 0

    average_lines = total_lines / file_count
    print(f"YAML files: {file_count}")
    print(f"Total lines: {total_lines}")
    print(f"Average lines per file: {average_lines:.2f}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
