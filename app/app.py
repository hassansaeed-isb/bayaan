from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import mysql.connector
from .config import DATABASE_CONFIG, API_TITLE, API_DESCRIPTION, API_VERSION

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# -------------------------
# Database Connection
# -------------------------

def get_db():
    return mysql.connector.connect(**DATABASE_CONFIG)

# -------------------------
# Models
# -------------------------

class Segment(BaseModel):
    start: int = Field(..., description="Starting word index (inclusive)", example=1)
    end: int = Field(..., description="Ending word index (inclusive)", example=10)
    text: str = Field(..., description="Translation text for this segment")

class SegmentRequest(BaseModel):
    translation_id: int = Field(..., example=1)
    surah_id: int = Field(..., example=2)
    ayah_number: int = Field(..., example=177)
    segments: list[Segment]

# -------------------------
# Get Ayah Words
# -------------------------

@app.get(
    "/ayah/{surah_id}/{ayah_number}",
    summary="Get Ayah Words",
    description="Fetch all Arabic words for a given Surah and Ayah"
)
def get_ayah(surah_id: int, ayah_number: int):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT word_index, text
        FROM ayah_words
        WHERE surah_id=%s AND ayah_number=%s
        ORDER BY word_index
    """, (surah_id, ayah_number))

    words = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "surah": surah_id,
        "ayah": ayah_number,
        "words": words
    }

# -------------------------
# Get Segments
# -------------------------

@app.get(
    "/segments/{translation_id}/{surah_id}/{ayah_number}",
    summary="Get Translation Segments",
    description="Retrieve segmented translation for a specific ayah"
)
def get_segments(translation_id: int, surah_id: int, ayah_number: int):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT segment_index, word_start, word_end, translation_text
        FROM translation_segments
        WHERE translation_id=%s AND surah_id=%s AND ayah_number=%s
        ORDER BY segment_index
    """, (translation_id, surah_id, ayah_number))

    segments = cursor.fetchall()

    cursor.close()
    conn.close()

    return segments

# -------------------------
# Create / Update Segments
# -------------------------

@app.post(
    "/segments",
    summary="Create or Update Segments",
    description="Replaces all segments for a given ayah and translation"
)
def create_segments(data: SegmentRequest):
    conn = get_db()
    cursor = conn.cursor()

    # Remove existing segments (overwrite strategy)
    cursor.execute("""
        DELETE FROM translation_segments
        WHERE translation_id=%s AND surah_id=%s AND ayah_number=%s
    """, (data.translation_id, data.surah_id, data.ayah_number))

    # Insert new segments
    for i, seg in enumerate(data.segments, start=1):
        if seg.start > seg.end:
            raise HTTPException(status_code=400, detail="start cannot be greater than end")

        cursor.execute("""
            INSERT INTO translation_segments (
                surah_id, ayah_number, translation_id,
                segment_index, word_start, word_end, translation_text
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data.surah_id,
            data.ayah_number,
            data.translation_id,
            i,
            seg.start,
            seg.end,
            seg.text
        ))

    conn.commit()
    cursor.close()
    conn.close()

    return {"status": "success"}