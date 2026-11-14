#!/usr/bin/env python3
"""Minimal GRF v2 packer for OzRagnarok custom files.

Usage:
  python3 tools/grf_pack.py --out ozro.grf \
      --root data=patch3/data \
      --root SystemEN=patch3/SystemEN
"""

from __future__ import annotations

import argparse
import os
import struct
import zlib
from pathlib import Path

HEADER_SIZE = 0x2E
GRF_MAGIC = b"Master of Magic\x00"


WRONG_TEXTURE_PREFIX = "À¯ÀúÀÎÅÍÆäÀÌ½º".encode("utf-8")
RIGHT_TEXTURE_PREFIX = "유저인터페이스".encode("cp949")


def iter_files(root: bytes, prefix: bytes):
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            full = os.path.join(dirpath, filename)
            rel = os.path.relpath(full, root).replace(b"/", b"\\")
            name = (prefix + b"\\" + rel) if prefix else rel
            name = name.replace(WRONG_TEXTURE_PREFIX, RIGHT_TEXTURE_PREFIX)
            yield name, full


def pack(out_path: Path, roots: list[tuple[str, Path]]) -> None:
    files: list[tuple[bytes, bytes]] = []
    for prefix, root in roots:
        root_b = os.fsencode(root)
        files.extend(iter_files(root_b, prefix.encode("ascii")))

    files.sort(key=lambda item: item[0].lower())

    data_blob = bytearray()
    entries: list[tuple[bytes, int, int, int, int, int]] = []
    for name, full in files:
        raw = Path(os.fsdecode(full)).read_bytes()
        compressed = zlib.compress(raw, 9)
        srclen = len(compressed)
        aligned = (srclen + 3) & ~3
        srcpos = len(data_blob)
        data_blob += compressed
        data_blob += b"\x00" * (aligned - srclen)
        entries.append((name, srclen, aligned, len(raw), 0x01, srcpos))

    table = bytearray()
    for name, srclen, aligned, declen, typ, srcpos in entries:
        table += name + b"\x00"
        table += struct.pack("<III", srclen, aligned, declen)
        table += bytes([typ])
        table += struct.pack("<I", srcpos)

    compressed_table = zlib.compress(bytes(table), 9)
    table_offset = len(data_blob)

    header = bytearray()
    header += GRF_MAGIC
    header += bytes(range(1, 15))
    header += struct.pack("<I", table_offset)
    header += struct.pack("<I", 0)
    header += struct.pack("<I", len(entries) + 7)
    header += struct.pack("<I", 0x00000200)
    assert len(header) == HEADER_SIZE

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as handle:
        handle.write(header)
        handle.write(data_blob)
        handle.write(struct.pack("<II", len(compressed_table), len(table)))
        handle.write(compressed_table)

    print(f"{out_path}: {len(entries)} entries, {out_path.stat().st_size} bytes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--root",
        action="append",
        required=True,
        help="prefix=path (repeatable), e.g. data=patch3/data",
    )
    args = parser.parse_args()

    roots: list[tuple[str, Path]] = []
    for value in args.root:
        prefix, path = value.split("=", 1)
        roots.append((prefix, Path(path)))

    pack(Path(args.out), roots)


if __name__ == "__main__":
    main()
