# Bayaan API (FastAPI Backend)

This is the backend API for **Bayaan**, a Quran segmentation and alignment system.

It provides endpoints to:

- Fetch Quran ayah words
- Fetch translation segments
- Create/update translation segments

---

## 🚀 Tech Stack

- Python 3.10+
- FastAPI
- MySQL
- Uvicorn (ASGI server)

---

## 📚 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| **fastapi** | Latest | Web framework for building the API |
| **uvicorn** | Latest | ASGI server to run the FastAPI application |
| **pydantic** | Latest | Data validation and settings management |
| **mysql-connector-python** | Latest | MySQL database driver for Python |
| **python-dotenv** | Latest | Load environment variables from .env file |

---

## 📦 Installation

### 1. Clone the project

```bash
git clone <your-repo-url>
cd bayaan-backend
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install fastapi uvicorn mysql-connector-python python-dotenv pydantic
```

### 4. Configure Database

Update your DB credentials in app.py:

```
host="localhost",
user="root",
password="your_password",
database="bayaan"
```

## ▶️ Running the Server

```bash
uvicorn app.app:app --reload
```

## 🌐 Access Points
API Base:
http://127.0.0.1:8000
Swagger Docs (Interactive):
http://127.0.0.1:8000/docs
ReDoc (Alternative Docs):
http://127.0.0.1:8000/redoc
📡 API Endpoints
1. Get Ayah Words
GET /ayah/{surah_id}/{ayah_number}
Description:

Fetches all Arabic words of a given ayah.

Example:
GET /ayah/2/255
Response:
{
  "surah": 2,
  "ayah": 255,
  "words": [
    { "word_index": 1, "text": "اللَّهُ" },
    { "word_index": 2, "text": "لَا" }
  ]
}
2. Get Translation Segments
GET /segments/{translation_id}/{surah_id}/{ayah_number}
Description:

Returns all segments for a specific translation of an ayah.

3. Create / Update Segments
POST /segments
Description:

Creates or replaces all segments for a given ayah + translation.

Request Body:
{
  "translation_id": 1,
  "surah_id": 2,
  "ayah_number": 177,
  "segments": [
    { "start": 1, "end": 10, "text": "..." },
    { "start": 11, "end": 25, "text": "..." }
  ]
}
⚠️ Important Notes
Overwrite Behavior
Existing segments are deleted before inserting new ones
This ensures consistency
Validation (Future Work)

Currently minimal validation is applied.

Should add:

No overlapping segments
No gaps (optional)
Valid word ranges
🧠 Architecture Notes
Uses word-based segmentation
Avoids character indexing issues with Arabic
Segments map to word ranges:
word_index ∈ [start, end]
🛠️ Development Tips
Use Swagger UI to test endpoints quickly
Use Postman for advanced testing
Keep DB transactions clean
🔮 Next Steps
Build segment editor UI
Add validation layer
Add authentication (admin access)
Add caching for performance
📌 Summary

This API is the core backend for:

Quran word retrieval
Translation segmentation
Data alignment logic

---

# 🧩 Improved `app.py` (With Swagger Docs + Comments)

Here’s your **enhanced API with proper documentation**:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import mysql.connector

app = FastAPI(
    title="Bayaan API",
    description="API for Quran word retrieval and translation segment alignment",
    version="1.0.0"
)

# -------------------------
# Database Connection
# -------------------------

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",
        database="bayaan"
    )

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