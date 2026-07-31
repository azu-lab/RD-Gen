#!/usr/bin/env python3
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import yaml


@dataclass
class Counts:
    sources: int = 0
    sinks: int = 0
    intermediates: int = 0

    @property
    def total(self) -> int:
        return self.sources + self.sinks + self.intermediates


@dataclass
class LineTemplate:
    source: int
    sink: int
    intermediate: int


def iter_yaml_files(root_dir: Path) -> Iterable[Path]:
    for path in root_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}:
            yield path


def count_non_empty_lines(file_path: Path) -> int:
    count = 0
    with file_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def build_link_map(links: List[Dict]) -> Dict[int, Dict[str, List[int]]]:
    link_map: Dict[int, Dict[str, List[int]]] = {}
    for link in links:
        try:
            source = int(link["source"])
            target = int(link["target"])
        except (KeyError, TypeError, ValueError):
            continue

        link_map.setdefault(source, {"out": [], "in": []})["out"].append(target)
        link_map.setdefault(target, {"out": [], "in": []})["in"].append(source)
    return link_map


def count_reactors_in_doc(doc: Dict) -> Counts:
    nodes = doc.get("nodes", []) if isinstance(doc, dict) else []
    links = doc.get("links", []) if isinstance(doc, dict) else []
    link_map = build_link_map(links)

    counts = Counts()

    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = node.get("id")
        if node_id is None:
            continue

        in_links = link_map.get(node_id, {}).get("in", [])
        out_links = link_map.get(node_id, {}).get("out", [])
        period = node.get("period")
        end_deadline = node.get("end_to_end_deadline")

        is_source = len(in_links) == 0 and len(out_links) > 0 and period is not None
        is_sink = len(out_links) == 0 and len(in_links) > 0 and end_deadline is not None

        if is_source:
            counts.sources += 1
        elif is_sink:
            counts.sinks += 1
        else:
            counts.intermediates += 1

    return counts


def count_reactors_in_file(file_path: Path) -> Counts:
    with file_path.open("r", encoding="utf-8", errors="replace") as handle:
        documents = [doc for doc in yaml.safe_load_all(handle) if doc is not None]

    counts = Counts()
    for doc in documents:
        doc_counts = count_reactors_in_doc(doc)
        counts.sources += doc_counts.sources
        counts.sinks += doc_counts.sinks
        counts.intermediates += doc_counts.intermediates

    return counts


def is_counted_line(line: str) -> bool:
    return bool(line.strip())


def extract_template_blocks(lines: List[str]) -> List[Tuple[str, int]]:
    blocks: List[Tuple[str, int]] = []
    in_block = False
    block_type = ""
    block_line_count = 0

    for line in lines:
        if not in_block:
            if "register_periodic_reactor" in line:
                in_block = True
                block_type = "source"
                block_line_count = 0
            elif "register_sink_reactor" in line:
                in_block = True
                block_type = "sink"
                block_line_count = 0
            elif "register_reactor" in line:
                in_block = True
                block_type = "intermediate"
                block_line_count = 0

        if in_block:
            if is_counted_line(line):
                block_line_count += 1
            if ".await;" in line:
                blocks.append((block_type, block_line_count))
                in_block = False
                block_type = ""
                block_line_count = 0

    return blocks


def compute_line_template(template_path: Path) -> LineTemplate:
    with template_path.open("r", encoding="utf-8", errors="replace") as handle:
        lines = handle.readlines()

    blocks = extract_template_blocks(lines)
    if not blocks:
        raise ValueError("No register_* blocks found in template file.")

    source_counts = [count for kind, count in blocks if kind == "source"]
    sink_counts = [count for kind, count in blocks if kind == "sink"]
    intermediate_counts = [count for kind, count in blocks if kind == "intermediate"]

    if not source_counts or not sink_counts or not intermediate_counts:
        raise ValueError("Template file missing source/sink/intermediate blocks.")

    return LineTemplate(
        source=sum(source_counts) // len(source_counts),
        sink=sum(sink_counts) // len(sink_counts),
        intermediate=sum(intermediate_counts) // len(intermediate_counts),
    )


def estimate_lines(counts: Counts, template: LineTemplate) -> int:
    return (
        counts.sources * template.source
        + counts.sinks * template.sink
        + counts.intermediates * template.intermediate
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate generated DAG code lines per YAML based on test_dag reactor blocks."
        )
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="test",
        help="Directory to scan (default: test)",
    )
    parser.add_argument(
        "--template",
        default="../awkernel3/applications/tests/test_dag/src/lib.rs",
        help="Path to test_dag-like template source file",
    )
    parser.add_argument(
        "--min-lines",
        type=int,
        default=10,
        help="Ignore YAML files with fewer non-empty lines than this (default: 10)",
    )
    args = parser.parse_args()

    root_dir = Path(args.directory)
    if not root_dir.exists():
        print(f"Directory not found: {root_dir}")
        return 1

    template_path = Path(args.template)
    if not template_path.exists():
        print(f"Template file not found: {template_path}")
        return 1

    try:
        template = compute_line_template(template_path)
    except ValueError as exc:
        print(f"Template error: {exc}")
        return 1

    total_estimated = 0
    total_nodes = 0
    file_count = 0
    dir_totals: Dict[Path, List[int]] = {}

    for yaml_file in sorted(iter_yaml_files(root_dir)):
        if count_non_empty_lines(yaml_file) < args.min_lines:
            continue
        counts = count_reactors_in_file(yaml_file)
        estimated = estimate_lines(counts, template)

        file_count += 1
        total_estimated += estimated
        total_nodes += counts.total

        rel_dir = yaml_file.parent.relative_to(root_dir)
        dir_totals.setdefault(rel_dir, []).append(estimated)

        print(
            f"{yaml_file}: sources={counts.sources}, "
            f"sinks={counts.sinks}, intermediates={counts.intermediates}, "
            f"estimated_lines={estimated}"
        )

    if file_count == 0:
        print("No YAML files found.")
        return 0

    avg_total = total_estimated / file_count
    avg_nodes = total_nodes / file_count
    print("---")
    print(f"YAML files: {file_count}")
    print(f"Estimated total lines: {total_estimated}")
    print(f"Estimated average lines per file: {avg_total:.2f}")
    print(f"Average nodes per file: {avg_nodes:.2f}")

    print("---")
    print("Per-directory totals:")
    for rel_dir in sorted(dir_totals.keys()):
        estimates = dir_totals[rel_dir]
        dir_total = sum(estimates)
        dir_avg = dir_total / len(estimates)
        display_dir = str(rel_dir) if str(rel_dir) != "." else "(root)"
        print(
            f"{display_dir}: files={len(estimates)}, total={dir_total}, average={dir_avg:.2f}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
