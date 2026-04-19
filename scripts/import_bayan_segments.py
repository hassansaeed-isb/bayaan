"""
Import Bayan ul Quran Urdu segments from exported .txt (InPage / unicode workflow)
into translation_segments for the API.

Requires ayah_words populated for the surah (same script as word import).

Usage (from repo root, venv active):

    python scripts/import_bayan_segments.py "bayan ul quran/.../output/al-baqara-1.txt"
    python scripts/import_bayan_segments.py "path/to/file.txt" --surah 2 --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import mysql.connector

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from app.bayan_parse import (
    align_snippet_to_words,
    dedupe_segments,
    iter_raw_segments,
    surah_id_from_filename,
)
from app.config import DATABASE_CONFIG


def import_segments_from_file(
    txt_path: Path,
    *,
    translation_id: int = 1,
    surah_id: int | None = None,
    dry_run: bool = False,
    text_override: str | None = None,
    filename_for_surah: str | None = None,
) -> int:
    """
    Parse Bayan export text and upsert translation_segments for one surah.

    ``txt_path`` is used for logging and reading unless ``text_override`` is set.

    ``filename_for_surah`` defaults to ``txt_path.name`` and is passed to
    ``surah_id_from_filename`` when ``surah_id`` is None (docx extraction should pass the original filename).
    """
    if text_override is None:
        if not txt_path.is_file():
            print("File not found:", txt_path, file=sys.stderr)
            return 1
        text = txt_path.read_text(encoding="utf-8")
    else:
        text = text_override

    name_for_surah = filename_for_surah if filename_for_surah is not None else txt_path.name
    resolved_surah = surah_id if surah_id is not None else surah_id_from_filename(name_for_surah)
    if resolved_surah is None:
        print(
            "Could not infer surah from filename %r; pass surah_id explicitly." % (name_for_surah,),
            file=sys.stderr,
        )
        return 1

    raw = dedupe_segments(iter_raw_segments(text))

    conn = mysql.connector.connect(**DATABASE_CONFIG)
    cursor = conn.cursor(dictionary=True)

    word_cache: dict[int, list[dict]] = {}

    def words_for(ayah: int) -> list[dict]:
        if ayah not in word_cache:
            word_cache[ayah] = _load_words(cursor, resolved_surah, ayah)
        return word_cache[ayah]

    aligned = 0
    skipped = 0
    rows: list[tuple] = []
    seg_index: dict[int, int] = {}

    for seg in raw:
        ayah = seg.ayah_number
        words = words_for(ayah)
        if not words:
            skipped += 1
            continue
        span = align_snippet_to_words(words, seg.arabic_raw)
        if not span:
            skipped += 1
            continue
        w0, w1 = span
        seg_index[ayah] = seg_index.get(ayah, 0) + 1
        idx = seg_index[ayah]
        aligned += 1
        rows.append(
            (
                resolved_surah,
                ayah,
                translation_id,
                idx,
                w0,
                w1,
                seg.urdu_raw,
            )
        )

    cursor.close()

    print(
        "%s — Surah %s: parsed %s snippets, aligned %s, skipped %s (missing words or no span match)."
        % (txt_path, resolved_surah, len(raw), aligned, skipped)
    )

    if dry_run:
        conn.close()
        return 0

    if not rows:
        print("Nothing to insert (populate ayah_words first).", file=sys.stderr)
        conn.close()
        return 1

    cursor = conn.cursor()
    ayahs_written = sorted({r[1] for r in rows})
    for ayah in ayahs_written:
        cursor.execute(
            """
            DELETE FROM translation_segments
            WHERE translation_id=%s AND surah_id=%s AND ayah_number=%s
            """,
            (translation_id, resolved_surah, ayah),
        )

    cursor.executemany(
        """
        INSERT INTO translation_segments (
            surah_id, ayah_number, translation_id,
            segment_index, word_start, word_end, translation_text
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
    )
    conn.commit()
    cursor.close()
    conn.close()
    print("Inserted %s segment row(s) across ayah(s): %s." % (len(rows), ayahs_written))
    return 0


def _load_words(cursor, surah_id: int, ayah: int) -> list[dict]:
    cursor.execute(
        """
        SELECT word_index, text FROM ayah_words
        WHERE surah_id=%s AND ayah_number=%s
        ORDER BY word_index
        """,
        (surah_id, ayah),
    )
    return list(cursor.fetchall())


def main() -> int:
    p = argparse.ArgumentParser(description="Import Bayan ul Quran segments from .txt export.")
    p.add_argument("txt_path", type=Path, help="Path to exported .txt (e.g. output/al-baqara-1.txt)")
    p.add_argument("--translation-id", type=int, default=1, help="translations.id (default: 1 bayan-ul-quran)")
    p.add_argument("--surah", type=int, default=None, help="Override surah id (else inferred from filename)")
    p.add_argument("--dry-run", action="store_true", help="Parse and match only; do not write DB")
    args = p.parse_args()

    return import_segments_from_file(
        args.txt_path,
        translation_id=args.translation_id,
        surah_id=args.surah,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
