#!/usr/bin/env python3
"""Split msgstringtable.txt into fixed-size chunks, preserving bytes/CRLF.

Examples:
  python3 tools/i18n_split.py patch/data/msgstringtable.txt tmp/i18n/src
  python3 tools/i18n_split.py patch/data/msgstringtable.txt tmp/i18n/src --lines 400
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("src", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--lines", type=int, default=400)
    args = parser.parse_args()

    if args.lines < 1:
        parser.error("--lines debe ser >= 1")

    data = args.src.read_bytes()
    lines = data.splitlines(keepends=True)
    if b"".join(lines) != data:
        parser.error(f"no se pudo partir {args.src} sin perder bytes")
    if not all(line.endswith(b"\r\n") for line in lines):
        parser.error(f"{args.src} tiene líneas sin CRLF")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    width = max(4, len(str((len(lines) + args.lines - 1) // args.lines)))
    count = 0
    for start in range(0, len(lines), args.lines):
        count += 1
        chunk = lines[start : start + args.lines]
        path = args.out_dir / f"{count:0{width}d}.txt"
        path.write_bytes(b"".join(chunk))
        print(f"{path} lineas={len(chunk)}")

    print(f"total_lineas={len(lines)} chunks={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
