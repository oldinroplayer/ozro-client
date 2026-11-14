#!/usr/bin/env python3
"""Extrae los assets basicos de un mapa desde un GRF a staging/maps/<map>/.

Uso:
  python3 tools/extract_map.py --grf /ruta/data.grf --map jupe_core2
  python3 tools/extract_map.py --grf /ruta/data.grf --map jupe_core2 --install

--install copia los archivos a /mnt/games/OzRo/data/ para probar en el cliente.
No sigue las referencias del .rsw a modelos/texturas.
"""
import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRFTOOL = os.path.join(ROOT, "tools", "grf.py")
STAGING = os.path.join(ROOT, "staging", "maps")
CLIENT_DATA = "/mnt/games/OzRo/data"
EXTS = (".gat", ".rsw", ".gnd")


def extract(grf, entry, out):
    r = subprocess.run(
        [sys.executable, GRFTOOL, "extract", grf, entry, "--out", out],
        capture_output=True,
        text=True,
    )
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grf", required=True, help="GRF de origen")
    ap.add_argument("--map", required=True, help="nombre del mapa, sin extension")
    ap.add_argument("--install", action="store_true", help="copiar a %s" % CLIENT_DATA)
    args = ap.parse_args()

    outdir = os.path.join(STAGING, args.map, "data")
    os.makedirs(outdir, exist_ok=True)

    found, missing = [], []
    for ext in EXTS:
        entry = "data/%s%s" % (args.map, ext)
        out = os.path.join(outdir, args.map + ext)
        if extract(args.grf, entry, out):
            found.append(ext)
        else:
            missing.append(ext)

    print("%s: encontrados %s; faltan %s" % (args.map, found or "-", missing or "-"))
    print("staging: %s" % outdir)

    if missing:
        print("Ojo: faltan extensiones; el mapa puede no cargar o cargar incompleto.")

    if args.install:
        os.makedirs(CLIENT_DATA, exist_ok=True)
        for name in os.listdir(outdir):
            shutil.copy2(os.path.join(outdir, name), os.path.join(CLIENT_DATA, name))
        print("instalado en %s (probar y borrar si falla)" % CLIENT_DATA)

    print("Dependencias del .rsw (modelos/texturas) no se extraen automaticamente.")


if __name__ == "__main__":
    main()
