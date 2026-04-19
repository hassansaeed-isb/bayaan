"""
Populate `ayah_words` (and `ayahs`) from either:

1) Quran.com API v4 — IndoPak word text (default), or
2) Legacy JSON dict (same keys as historical `indopak-nastaleeq.json`).

Run from repository root:

    python data/import-quran-aya-words.py --chapter 2
    python data/import-quran-aya-words.py --all-chapters

Requires `app/.env` with valid MySQL credentials (see `app/.env.example`).
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
import urllib.request
from pathlib import Path

import mysql.connector

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from app.config import DATABASE_CONFIG

API_BASE = "https://api.quran.com/api/v4"


def _ctx() -> ssl.SSLContext:
    return ssl.create_default_context()


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "bayaan-import/1.0"})
    with urllib.request.urlopen(req, timeout=120, context=_ctx()) as r:
        return json.loads(r.read().decode("utf-8"))


def _connect():
    return mysql.connector.connect(**DATABASE_CONFIG)


def import_chapter_api(conn, chapter_id: int) -> tuple[int, int]:
    """Return (rows_inserted_or_replaced, verses_touched)."""
    cursor = conn.cursor()
    rows = 0
    verses = set()
    page = 1
    per_page = 50

    while True:
        url = (
            f"{API_BASE}/verses/by_chapter/{chapter_id}"
            f"?words=true&word_fields=text_indopak"
            f"&per_page={per_page}&page={page}"
        )
        data = _fetch_json(url)
        for verse in data.get("verses") or []:
            vnum = int(verse["verse_number"])
            verses.add(vnum)
            wid = 0
            for w in verse.get("words") or []:
                ctype = (w.get("char_type_name") or "").lower()
                if ctype not in ("word", "end"):
                    continue
                text = (w.get("text_indopak") or w.get("text") or "").strip()
                if not text:
                    continue
                wid += 1
                is_sym = 1 if ctype == "end" or len(text) <= 2 else 0
                wid_api = int(w["id"])
                loc = f"{chapter_id}:{vnum}:{wid}"
                cursor.execute(
                    "INSERT IGNORE INTO ayahs (surah_id, ayah_number) VALUES (%s, %s)",
                    (chapter_id, vnum),
                )
                cursor.execute(
                    """
                    REPLACE INTO ayah_words (
                        id, surah_id, ayah_number, word_index, location, text, is_symbol
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (wid_api, chapter_id, vnum, wid, loc, text, is_sym),
                )
                rows += 1
        pag = data.get("pagination") or {}
        total_pages = int(pag.get("total_pages") or 1)
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.15)

    conn.commit()
    cursor.close()
    return rows, len(verses)


def import_legacy_json(conn, json_path: Path) -> int:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    cursor = conn.cursor()
    ayah_set: set[tuple[int, int]] = set()
    rows = 0
    for _key, value in data.items():
        surah = int(value["surah"])
        ayah = int(value["ayah"])
        word_index = int(value["word"])
        location = value["location"]
        text = value["text"]
        word_id = int(value["id"])
        if (surah, ayah) not in ayah_set:
            cursor.execute(
                "INSERT IGNORE INTO ayahs (surah_id, ayah_number) VALUES (%s, %s)",
                (surah, ayah),
            )
            ayah_set.add((surah, ayah))
        is_symbol = 1 if len(text.strip()) <= 2 else 0
        cursor.execute(
            """
            REPLACE INTO ayah_words (
                id, surah_id, ayah_number, word_index, location, text, is_symbol
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (word_id, surah, ayah, word_index, location, text, is_symbol),
        )
        rows += cursor.rowcount
    conn.commit()
    cursor.close()
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Import Quran words into ayah_words.")
    ap.add_argument(
        "--legacy-json",
        type=Path,
        default=None,
        help="Path to flat JSON (historical indopak dump); if set, API mode is disabled.",
    )
    ap.add_argument(
        "--chapter",
        type=int,
        default=None,
        help="Import one surah via Quran.com API (e.g. 2 for Al-Baqarah).",
    )
    ap.add_argument(
        "--all-chapters",
        action="store_true",
        help="Import all 114 surahs via API (many HTTP requests).",
    )
    args = ap.parse_args()

    if args.legacy_json is not None:
        if not args.legacy_json.is_file():
            print("JSON not found:", args.legacy_json, file=sys.stderr)
            return 1
        conn = _connect()
        n = import_legacy_json(conn, args.legacy_json)
        conn.close()
        print("Legacy import finished; row operations (approx):", n)
        return 0

    if args.all_chapters:
        chapters = range(1, 115)
    elif args.chapter is not None:
        chapters = (args.chapter,)
    else:
        print("Specify --chapter N and/or --all-chapters, or --legacy-json PATH", file=sys.stderr)
        return 1

    conn = _connect()
    total_r = 0
    for c in chapters:
        r, nv = import_chapter_api(conn, c)
        total_r += r
        print(f"Chapter {c}: rows ~{r}, verses {nv}")
    conn.close()
    print("Done. Total row touches:", total_r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
