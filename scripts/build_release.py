"""Create a ZIP release artifact for the current repository state.
Excludes virtualenv, .git, and large model assets if desired.
Usage: python scripts/build_release.py --out dist/nebula-interface-v1.0.zip
"""

import argparse
import os
import zipfile
from pathlib import Path

EXCLUDE_DIRS = {".git", "dist", ".venv", "__pycache__", "assets/models"}


def should_exclude(path: Path):
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return True
    return False


def build_zip(root: Path, out: Path):
    root = root.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(root):
            p = Path(dirpath)
            # skip excluded dirs
            if should_exclude(p.relative_to(root)):
                continue
            for fname in filenames:
                fp = p / fname
                rel = fp.relative_to(root)
                if should_exclude(rel):
                    continue
                zf.write(fp, arcname=str(rel))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = Path(args.out)
    print(f"Building release ZIP: {out}")
    build_zip(root, out)
    print("Done")


if __name__ == "__main__":
    main()
