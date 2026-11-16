#!/usr/bin/env python3
"""Build the OzRo card-book atlas and catalog.

Inputs:
  - rAthena Card Collector NPC (source of categories/order)
  - rAthena item DB (card names)
  - tools/cardbmp-map.json (confirmed itemId -> cardbmp filename)
  - an extracted cardbmp directory (300x400 BMP files)

Outputs (default: ../ozro-site/assets/cards):
  - atlas_<n>.<hash>.webp
  - catalog.json
  - build-report.json

The cardbmp files are extracted from data.grf separately. The review
tooling used for the initial extraction lives in
`ozro-cli/tmp/card-review/tools/` and uses a DES-capable GRF reader.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

CODE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NPC = CODE_ROOT / "rathena/npc/custom/ozro/card_collector.txt"
DEFAULT_ITEM_DB = CODE_ROOT / "rathena/db"
DEFAULT_MAPPING = Path(__file__).with_name("cardbmp-map.json")
DEFAULT_CARDBMP = Path("/tmp/cardbmp-all")
DEFAULT_OUT = CODE_ROOT / "ozro-site/assets/cards"

CATEGORY_ORDER = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N",
    "O", "P", "Q", "R", "S", "T", "U", "V", "W", "Y", "Z", "BOSS", "MVP",
]


def parse_categories(path: Path) -> list[tuple[str, list[int]]]:
    text = path.read_text(encoding="latin-1")
    result = []
    for code, body in re.findall(r"setarray \.card_arr_(\w+),\s*([0-9,\s]+);", text):
        result.append((code, [int(x) for x in re.findall(r"\d+", body)]))
    order = {code: index for index, code in enumerate(CATEGORY_ORDER)}
    result.sort(key=lambda item: order.get(item[0], 999))
    return result


def parse_item_names(db_root: Path) -> dict[int, str]:
    names: dict[int, str] = {}
    for pattern in ("re/item_db_*.yml", "import/item_db*.yml"):
        for path in db_root.glob(pattern):
            current = None
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                match = re.match(r"\s*- Id: (\d+)", line)
                if match:
                    current = int(match.group(1))
                    continue
                if current is None:
                    continue
                match = re.match(r"\s+Name: (.+)", line)
                if match:
                    names[current] = match.group(1).strip()
    return names


def page_group(code: str) -> int:
    return 1 if code in ("BOSS", "MVP") else 0


def save_hashed_webp(image: Image.Image, out_dir: Path, index: int, quality: int) -> str:
    temp = out_dir / f".atlas_{index}.tmp.webp"
    image.save(temp, "WEBP", quality=quality, method=6)
    digest = hashlib.sha1(temp.read_bytes()).hexdigest()[:10]
    filename = f"atlas_{index}.{digest}.webp"
    target = out_dir / filename
    temp.replace(target)
    return filename


def main() -> int:
    parser = argparse.ArgumentParser(description="Build card-book atlas and catalog")
    parser.add_argument("--npc", type=Path, default=DEFAULT_NPC)
    parser.add_argument("--item-db", type=Path, default=DEFAULT_ITEM_DB)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--cardbmp-dir", type=Path, default=DEFAULT_CARDBMP)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--tile-width", type=int, default=150)
    parser.add_argument("--tile-height", type=int, default=200)
    parser.add_argument("--columns", type=int, default=20)
    parser.add_argument("--quality", type=int, default=86)
    args = parser.parse_args()

    if not args.cardbmp_dir.is_dir():
        raise SystemExit(f"cardbmp directory not found: {args.cardbmp_dir}")
    if not args.mapping.is_file():
        raise SystemExit(f"mapping file not found: {args.mapping}")

    categories = parse_categories(args.npc)
    item_names = parse_item_names(args.item_db)
    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))

    seen: set[int] = set()
    catalog_categories = []
    cards_by_page: dict[int, list[dict]] = {0: [], 1: [], 2: [], 3: []}
    missing_mapping = []
    missing_art = []

    for code, ids in categories:
        cards = []
        for item_id in ids:
            if item_id in seen:
                continue
            seen.add(item_id)
            filename = mapping.get(str(item_id))
            if not filename:
                missing_mapping.append(item_id)
                continue
            source = args.cardbmp_dir / filename
            if not source.is_file():
                missing_art.append((item_id, filename))
                continue
            name = item_names.get(item_id, f"Item {item_id}")
            card = {
                "id": item_id,
                "name": name,
                "_source": source,
                "_category": code,
            }
            cards.append(card)
            cards_by_page[page_group(code)].append(card)
        cards.sort(key=lambda card: (card["name"].casefold(), card["id"]))
        catalog_categories.append(
            {
                "code": code,
                "label": code,
                "cards": cards,
            }
        )

    if missing_mapping:
        raise SystemExit(f"cards without a cardbmp mapping: {missing_mapping}")
    if missing_art:
        raise SystemExit(f"cardbmp files not found: {missing_art}")

    args.out.mkdir(parents=True, exist_ok=True)
    for stale in args.out.glob("atlas_*.webp"):
        stale.unlink()

    tile_w, tile_h = args.tile_width, args.tile_height
    cell_w, cell_h = tile_w + 1, tile_h + 1
    pages = []
    page_index_by_group: dict[int, int] = {}

    for group, page_cards in cards_by_page.items():
        if not page_cards:
            continue
        page_index = len(pages)
        page_index_by_group[group] = page_index
        columns = min(args.columns, len(page_cards))
        rows = math.ceil(len(page_cards) / columns)
        width, height = columns * cell_w, rows * cell_h
        atlas = Image.new("RGB", (width, height), (255, 255, 255))

        for position, card in enumerate(page_cards):
            image = Image.open(card["_source"]).convert("RGB").resize(
                (tile_w, tile_h), Image.LANCZOS
            )
            x = (position % columns) * cell_w
            y = (position // columns) * cell_h
            atlas.paste(image, (x, y))
            card["_rect"] = {"x": x, "y": y, "w": tile_w, "h": tile_h, "page": page_index}

        image_name = save_hashed_webp(atlas, args.out, page_index, args.quality)
        pages.append(
            {
                "page": page_index,
                "image": image_name,
                "width": width,
                "height": height,
                "count": len(page_cards),
            }
        )

    catalog = {
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "total": sum(len(category["cards"]) for category in catalog_categories),
        "cardWidth": tile_w,
        "cardHeight": tile_h,
        "pages": pages,
        "categories": [],
    }

    for category in catalog_categories:
        output_cards = []
        for card in category["cards"]:
            rect = card["_rect"]
            output_cards.append(
                {
                    "id": card["id"],
                    "name": card["name"],
                    "page": rect["page"],
                    "x": rect["x"],
                    "y": rect["y"],
                    "w": rect["w"],
                    "h": rect["h"],
                }
            )
        catalog["categories"].append(
            {
                "code": category["code"],
                "label": category["label"],
                "cards": output_cards,
            }
        )

    catalog_path = args.out / "catalog.json"
    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report = {
        "generatedAt": catalog["generatedAt"],
        "total": catalog["total"],
        "pages": pages,
        "categories": [
            {"code": category["code"], "total": len(category["cards"])}
            for category in catalog["categories"]
        ],
        "source": {
            "npc": str(args.npc),
            "itemDb": str(args.item_db),
            "mapping": str(args.mapping),
            "cardbmpDir": str(args.cardbmp_dir),
        },
    }
    (args.out / "build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"cards: {catalog['total']}")
    print(f"pages: {len(pages)}")
    for page in pages:
        print(f"  page {page['page']}: {page['count']} cards, {page['width']}x{page['height']}, {page['image']}")
    print(f"output: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
