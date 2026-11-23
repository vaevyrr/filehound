#!/usr/bin/env python3
"""Find duplicate files by size and SHA-256 without changing the originals."""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

CHUNK_SIZE = 1024 * 1024

def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()

def walk_files(roots: Iterable[Path], include_hidden: bool = False):
    for root in roots:
        if not root.exists():
            print(f"Skipping missing path: {root}", file=sys.stderr)
            continue
        if root.is_file() and not root.is_symlink():
            yield root
            continue
        if not root.is_dir():
            continue
        for current, dirs, names in os.walk(root, followlinks=False):
            current_path = Path(current)
            dirs[:] = [
                name for name in dirs
                if not (current_path / name).is_symlink()
                and (include_hidden or not name.startswith("."))
            ]
            for name in names:
                path = current_path / name
                if path.is_symlink() or (not include_hidden and name.startswith(".")):
                    continue
                if path.is_file():
                    yield path

def find_duplicates(roots: list[Path], min_size: int = 1, include_hidden: bool = False):
    by_size: dict[int, list[Path]] = defaultdict(list)
    errors: list[tuple[str, str]] = []
    for path in walk_files(roots, include_hidden):
        try:
            size = path.stat().st_size
        except OSError as exc:
            errors.append((str(path), str(exc)))
            continue
        if size >= min_size:
            by_size[size].append(path)

    groups: dict[tuple[int, str], list[Path]] = defaultdict(list)
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        for path in paths:
            try:
                groups[(size, digest_file(path))].append(path)
            except OSError as exc:
                errors.append((str(path), str(exc)))

    duplicates = [
        {"size": size, "sha256": sha, "paths": sorted(map(str, paths))}
        for (size, sha), paths in groups.items() if len(paths) > 1
    ]
    duplicates.sort(key=lambda group: (-group["size"], group["paths"][0]))
    return duplicates, errors

def write_report(path: Path, groups: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["group", "size_bytes", "sha256", "path"])
        for number, group in enumerate(groups, 1):
            for filename in group["paths"]:
                writer.writerow([number, group["size"], group["sha256"], filename])

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find identical files in selected folders.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--min-size", type=int, default=1, help="ignore files smaller than this many bytes")
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--csv", type=Path, default=Path("duplicates.csv"))
    args = parser.parse_args(argv)
    if args.min_size < 0:
        parser.error("--min-size cannot be negative")
    groups, errors = find_duplicates(args.paths, args.min_size, args.include_hidden)
    for number, group in enumerate(groups, 1):
        saved = group["size"] * (len(group["paths"]) - 1)
        print(f"Group {number}: {len(group['paths'])} copies, {group['size']:,} bytes each ({saved:,} bytes redundant)")
        for path in group["paths"]:
            print(f"  {path}")
    for path, error in errors:
        print(f"Could not read {path}: {error}", file=sys.stderr)
    try:
        write_report(args.csv, groups)
    except OSError as exc:
        print(f"Could not write CSV: {exc}", file=sys.stderr)
        return 2
    print(f"\nFound {len(groups)} duplicate group(s). Report: {args.csv}")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
