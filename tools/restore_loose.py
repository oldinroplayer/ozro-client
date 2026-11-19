#!/usr/bin/env python3
"""Materialize the client files that the Lua VM opens from disk.

The GRF is the canonical artifact, but roBrowser's Lua layer uses io.open /
dofile for these files and does not read them from the GRF through the
Remote Client. Extract them into the deployed client folder after copying
the GRFs.

Usage:
  python3 tools/restore_loose.py --grf patch/ozro.grf --out "/mnt/games/OzRo"
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grf import Grf  # noqa: E402


FILES = (
    "System/itemInfo_EN.lua",
    "System/OngoingQuestInfoList_True_EN.lub",
    "System/Towninfo.lub",
    "System/Towninfo_EN.lub",
    "data/msgstringtable.txt",
    "data/luafiles514/lua files/signboardlist.lub",
    "data/luafiles514/lua files/datainfo/tb_cashshop_banner.lub",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grf", default="patch/ozro.grf")
    parser.add_argument("--out", required=True, help="deployed client folder")
    args = parser.parse_args()

    grf = Grf(args.grf)
    by_name = {entry.name: entry for entry in grf.entries}
    missing = [name for name in FILES if name not in by_name]
    if missing:
        for name in missing:
            print("missing in GRF: " + name, file=sys.stderr)
        return 1

    for name in FILES:
        entry = by_name[name]
        out = os.path.join(os.fsencode(args.out), entry.name_bytes.replace(b"\\", b"/"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as handle:
            handle.write(grf.read(entry))
        print("restored " + name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
