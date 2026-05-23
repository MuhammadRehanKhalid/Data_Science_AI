"""Small utility to find legacy `results`/`figures` folders and archive or remove them.

Usage:
  python tools/organize_outputs.py [--archive-dir ARCHIVE] [--dry-run] [--delete-empty]

This script is conservative: it moves non-empty legacy folders into an
archive directory under `HPLC_GCMS_Fingerprint/archived_outputs/<timestamp>/`.
If `--delete-empty` is provided, empty directories found will be deleted.
"""
from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path
import sys


def _repo_root() -> Path:
    # Resolve the repository root relative to this script location so the tool
    # works regardless of the current working directory or drive letter.
    return Path(__file__).resolve().parent.parent


LEGACY_PATHS = [
    _repo_root() / "figures",
    _repo_root() / "results",
    _repo_root() / "data" / "results",
    _repo_root() / Path("HPLC_GCMS_Fingerprint") / "data" / "results",
]


def find_existing(paths: list[Path]) -> list[Path]:
    existing = []
    for p in paths:
        if p.exists():
            existing.append(p)
    return existing


def archive_paths(
    paths: list[Path],
    archive_root: Path,
    repo_root: Path,
    dry_run: bool = True,
):
    moved = []
    for p in paths:
        if not p.exists():
            continue
        if any(p.iterdir()):
            # Preserve path structure relative to repo_root to avoid collisions
            # like data/results and nested/data/results both becoming "results".
            try:
                rel = p.relative_to(repo_root)
                target = archive_root / rel
            except ValueError:
                target = archive_root / p.name
            print(f"Archiving {p} -> {target}")
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), str(target))
            moved.append((p, target))
        else:
            print(f"Skipping empty directory {p}")
    return moved


def remove_empty(paths: list[Path], dry_run: bool = True):
    removed = []
    for p in paths:
        if p.exists() and not any(p.iterdir()):
            print(f"Removing empty directory {p}")
            if not dry_run:
                try:
                    p.rmdir()
                except Exception as e:
                    print(f"Failed to remove {p}: {e}")
            removed.append(p)
    return removed


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--delete-empty", action="store_true", default=False)
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_root = Path(args.archive_dir) if args.archive_dir else repo_root / "archived_outputs" / timestamp

    existing = find_existing(LEGACY_PATHS)
    if not existing:
        print("No legacy result/figure directories found.")
        return 0

    print("Found legacy directories:")
    for p in existing:
        print(f" - {p} (contains files: {any(p.iterdir())})")

    print(f"Archive root: {archive_root}")
    print("Dry run:" , args.dry_run)
    if args.dry_run:
        print("No changes will be made. Rerun without --dry-run to perform actions.")

    archive_paths(existing, archive_root, repo_root=repo_root, dry_run=args.dry_run)

    if args.delete_empty:
        remove_empty(existing, dry_run=args.dry_run)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
