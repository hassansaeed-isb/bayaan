"""
Parse Bayan ul Quran exported text (InPage / unicode workflow).

Structure: Urdu commentary pairs Arabic snippets in ornate brackets ﴿ ﴾
with translation in paired typographic quotes, e.g.:

    آیت ۲ ﴿ذٰلِکَ الْکِتٰبُ …﴾ ''یہ الکتاب ہے…''

Markers (A, B, …) inside brackets are segmentation hints from the source;
they are stripped before aligning to ayah_words.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Ornate parentheses used in Bayan ul Quran exports (Unicode names: ORNATE LEFT/RIGHT PARENTHESIS).
# Some InPage / export pipelines swap these glyphs; we accept either order.
OB = "\uFD3E"
CB = "\uFD3F"
_ORNATE = frozenset((OB, CB))

URDU_DIGIT_MAP = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹",
    "0123456789",
)

# Filename stem (lowercase) -> surah id. Extend as you add more exports.
FILENAME_TO_SURAH: dict[str, int] = {
    "al-baqara": 2,
    "al-baqarah": 2,
    "baqara": 2,
    "baqarah": 2,
    "al-fatihah": 1,
    "al-fatiha": 1,
    "fatiha": 1,
    "fatihah": 1,
    "al-imran": 3,
    "al-e-imran": 3,
    "ale-imran": 3,
    "an-nisa": 4,
    "an-nisaa": 4,
    "al-maidah": 5,
    "al-maida": 5,
    "al-anam": 6,
    "al-anaam": 6,
    "al-araf": 7,
    "al-aaraf": 7,
    "al-anfal": 8,
    "at-taubah": 9,
    "at-tawbah": 9,
    "yunus": 10,
    "hud": 11,
    "yusuf": 12,
    "ar-rad": 13,
    "ibrahim": 14,
    "al-hijr": 15,
    "an-nahl": 16,
    "al-isra": 17,
    "al-kahf": 18,
    "maryam": 19,
    "ta-ha": 20,
    "taha": 20,
}


@dataclass
class RawSegment:
    ayah_number: int
    arabic_raw: str
    urdu_raw: str
    source_line: int


def surah_id_from_filename(filename: str) -> int | None:
    stem = filename.rsplit(".", 1)[0].lower()
    stem = re.sub(r"[_-]extracted(?:-\d+)?$", "", stem)
    # al-baqara-1 -> al-baqara
    stem = re.sub(r"-\d+$", "", stem)
    stem = stem.strip().replace(" ", "-")
    return FILENAME_TO_SURAH.get(stem)


def _strip_diacritics(s: str) -> str:
    nkfd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nkfd if unicodedata.category(c) != "Mn")


def _parse_ayah_number(raw: str) -> int | None:
    raw = raw.strip().translate(URDU_DIGIT_MAP)
    raw = re.sub(r"\s+", " ", raw)
    if not raw:
        return None
    parts = raw.split()
    if len(parts) == 2 and len(parts[0]) == 1 and len(parts[1]) == 1 and parts[0].isdigit() and parts[1].isdigit():
        return int(parts[0]) * 10 + int(parts[1])
    digits = re.sub(r"[^\d]", "", raw.replace(" ", ""))
    if not digits:
        return None
    n = int(digits)
    return n if 1 <= n <= 286 else None


_AYAH_HEAD = re.compile(
    r"^\s*آیت\s*((?:[\d\u0660-\u0669\u06f0-\u06f9]\s*)+)",
)


def parse_ayah_heading(line: str) -> int | None:
    m = _AYAH_HEAD.match(line)
    if not m:
        return None
    return _parse_ayah_number(m.group(1))


def normalize_inpage_export(text: str) -> str:
    """
    InPage / Word saves often use doubled CR (`\\r\\r\\n`) and stray `\\r` inside paragraphs.
    Normalize to single `\\n` between logical lines so `splitlines()` matches editor line numbers.
    """
    s = text.replace("\r\r\n", "\n").replace("\r\n", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = s.replace("\r", "")
    return s


def clean_arabic_snippet(raw: str) -> str:
    t = raw.strip()
    t = re.sub(r"\s+[A-Z]\s+", " ", t)
    t = re.sub(r"([^\s])([A-Z])(?=\s*$)", r"\1", t)
    t = re.sub(r"([ء-ي])([A-Za-z])(?=\s*$)", r"\1", t)
    t = re.sub(r"(?<=[ء-ي])([a-z])(?=[ء-ي])", "", t)
    t = t.replace(OB, "").replace(CB, "")
    return t.strip()


_AR_CORE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+")


def ar_letters_core(s: str) -> str:
    s = _strip_diacritics(s)
    return "".join(_AR_CORE.findall(s))


def extract_quoted_urdu(line: str, after: int) -> tuple[str, int] | None:
    """After `after` index on line, find opening quote pair and closing pair; return (text, end_index)."""
    i = after
    n = len(line)
    while i < n and line[i] in " \t":
        i += 1
    if i + 1 >= n:
        return None
    q0, q1 = line[i], line[i + 1]
    quote_chars = frozenset("'\u2018\u2019\u201c\u201d")
    if q0 not in quote_chars or q1 not in quote_chars:
        return None
    # Urdu typesetting often uses ‘’ (U+2019+2019) to open and ‘’ (U+2018+2018) to close.
    close_pair = {
        ("\u2019", "\u2019"): ("\u2018", "\u2018"),
        ("\u2018", "\u2018"): ("\u2019", "\u2019"),
    }.get((q0, q1), (q0, q1))
    i += 2
    start = i
    c0, c1 = close_pair
    while i < n - 1:
        if line[i] == c0 and line[i + 1] == c1:
            return line[start:i].strip(), i + 2
        i += 1
    return None


def _next_ornate_pair(line: str, start: int) -> tuple[int, int] | None:
    """Inclusive start index of first ornate, inclusive end index of second ornate."""
    fo = -1
    for i in range(start, len(line)):
        if line[i] in _ORNATE:
            fo = i
            break
    if fo == -1:
        return None
    for j in range(fo + 1, len(line)):
        if line[j] in _ORNATE:
            return fo, j
    return None


def iter_snippets_with_quotes(line: str) -> list[tuple[str, str]]:
    """Return (arabic_inner, urdu) for each ornate pair followed by quoted Urdu."""
    out: list[tuple[str, str]] = []
    pos = 0
    while pos < len(line):
        pair = _next_ornate_pair(line, pos)
        if not pair:
            break
        fo, fc = pair
        inner = line[fo + 1 : fc].strip()
        if len(inner) < 1:
            pos = fc + 1
            continue
        quoted = extract_quoted_urdu(line, fc + 1)
        if quoted:
            urdu, end_ch = quoted
            if len(urdu.strip()) >= 2:
                out.append((inner, urdu.strip()))
            pos = end_ch
        else:
            pos = fc + 1
    return out


def iter_raw_segments(text: str) -> list[RawSegment]:
    text = normalize_inpage_export(text)
    current_ayah: int | None = None
    out: list[RawSegment] = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, start=1):
        h = parse_ayah_heading(line)
        if h is not None:
            current_ayah = h
        if current_ayah is None:
            continue
        for inner, urdu in iter_snippets_with_quotes(line):
            if len(urdu) < 2:
                continue
            out.append(
                RawSegment(
                    ayah_number=current_ayah,
                    arabic_raw=inner,
                    urdu_raw=urdu,
                    source_line=lineno,
                )
            )
    return out


def dedupe_segments(segments: list[RawSegment]) -> list[RawSegment]:
    seen: set[tuple[int, str, str]] = set()
    uniq: list[RawSegment] = []
    for s in segments:
        key = (s.ayah_number, ar_letters_core(clean_arabic_snippet(s.arabic_raw)), s.urdu_raw[:80])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(s)
    return uniq


def align_snippet_to_words(
    word_rows: list[dict],
    arabic_snippet: str,
) -> tuple[int, int] | None:
    """
    Map snippet to inclusive word_index range using stripped Arabic letter sequence.
    word_rows: rows with keys word_index, text (from ayah_words).
    """
    if not word_rows:
        return None
    cleaned = clean_arabic_snippet(arabic_snippet)
    needle = ar_letters_core(cleaned)
    if len(needle) < 2:
        return None
    cores = [ar_letters_core(r["text"]) for r in word_rows]
    full = "".join(cores)
    pos = full.find(needle)
    if pos < 0:
        for shrink in range(1, min(40, len(needle))):
            tail = needle[:-shrink]
            if len(tail) < 3:
                break
            pos = full.find(tail)
            if pos >= 0:
                needle = tail
                break
        if pos < 0:
            return None
    end_char = pos + len(needle) - 1
    acc = 0
    start_w = end_w = None
    for row, core in zip(word_rows, cores, strict=True):
        wlen = len(core)
        lo, hi = acc, acc + wlen - 1
        if start_w is None and lo <= pos <= hi:
            start_w = int(row["word_index"])
        if lo <= end_char <= hi:
            end_w = int(row["word_index"])
        acc += wlen
    if start_w is None or end_w is None:
        return None
    if start_w > end_w:
        start_w, end_w = end_w, start_w
    return start_w, end_w


def group_by_ayah(segments: list[RawSegment]) -> dict[int, list[RawSegment]]:
    g: dict[int, list[RawSegment]] = {}
    for s in segments:
        g.setdefault(s.ayah_number, []).append(s)
    return g
