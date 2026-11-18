#!/usr/bin/env python3
"""Validate translated msgstringtable chunks by structure, without printing text.

Checks per chunk: line count, CRLF endings, placeholder/color-code signature,
and byte-identical copy for lines with no letters. Also flags likely UTF-8.

Examples:
  python3 tools/validate_msgtable.py tmp/i18n/src tmp/i18n/out
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PLACEHOLDER = re.compile(rb"%[-+ 0#]*[0-9]*(?:\.[0-9]+)?[a-zA-Z%]")
COLOR = re.compile(rb"\^[0-9a-fA-F]{6}")
LETTER = re.compile(rb"[A-Za-z]")


def signature(line: bytes) -> tuple[bytes, ...]:
    return tuple(PLACEHOLDER.findall(line)) + tuple(COLOR.findall(line))


def has_letters(line: bytes) -> bool:
    return LETTER.search(PLACEHOLDER.sub(b"", COLOR.sub(b"", line))) is not None


def looks_utf8(data: bytes) -> bool:
    if data.isascii():
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def check_chunk(src: Path, out: Path) -> list[str]:
    errors: list[str] = []
    src_lines = src.read_bytes().splitlines(keepends=True)
    out_lines = out.read_bytes().splitlines(keepends=True)

    if len(src_lines) != len(out_lines):
        errors.append(f"lineas {len(out_lines)} != {len(src_lines)}")
        return errors

    for number, (a, b) in enumerate(zip(src_lines, out_lines), start=1):
        if not b.endswith(b"\r\n"):
            errors.append(f"linea {number}: sin CRLF")
            continue
        core_a, core_b = a[:-2], b[:-2]
        if not has_letters(a) and a != b:
            errors.append(f"linea {number}: linea sin letras modificada")
        if signature(a) != signature(b):
            errors.append(
                f"linea {number}: placeholders {signature(b)!r} != {signature(a)!r}"
            )
        if core_a[: len(core_a) - len(core_a.lstrip())] != core_b[
            : len(core_b) - len(core_b.lstrip())
        ]:
            errors.append(f"linea {number}: espacio inicial distinto")
        if core_a[len(core_a.rstrip()) :] != core_b[len(core_b.rstrip()) :]:
            errors.append(f"linea {number}: espacio final distinto")
        if has_letters(a) and core_a.endswith(b"#") != core_b.endswith(b"#"):
            errors.append(f"linea {number}: '#' final distinto")

    if looks_utf8(out.read_bytes()):
        errors.append("salida parece UTF-8 (se esperaba CP1252/ASCII)")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("src_dir", type=Path)
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args()

    sources = sorted(args.src_dir.glob("*.txt"))
    if not sources:
        parser.error(f"no hay chunks en {args.src_dir}")

    failed = 0
    for src in sources:
        out = args.out_dir / src.name
        if not out.exists():
            print(f"FALTA {out}")
            failed += 1
            continue
        errors = check_chunk(src, out)
        if errors:
            failed += 1
            print(f"FALLO {src.name}")
            for error in errors[:10]:
                print(f"  {error}")
            if len(errors) > 10:
                print(f"  ... {len(errors) - 10} mas")
        else:
            print(f"OK {src.name} ({len(src.read_bytes().splitlines())} lineas)")

    print(f"chunks={len(sources)} fallos={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
