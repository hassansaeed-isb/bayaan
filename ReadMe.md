# Bayaan

Bayaan is a Quran-focused web application designed to present the Arabic text of the Qur’an alongside its translations in a **structurally aligned and visually intuitive way**.

Unlike traditional Quran apps that display full translations below an entire ayah, Bayaan introduces a **segment-based alignment system**, where portions of an ayah are directly mapped to their corresponding translation—making it easier to study, explain, and understand the Qur’an.

---

## 🚀 Core Idea

The key innovation in Bayaan is:

> **Dynamic alignment between segments of Arabic text and their corresponding translation, rendered responsively across devices.**

### What makes it different?

- The Qur’an text is rendered **digitally (not images or PDFs)**
- Layout is **fully responsive** (mobile, tablet, desktop)
- Each **portion of an ayah** is mapped to its **exact translation**
- Supports **multiple translations**, each with its own segmentation
- Designed for **teaching, learning, and deep study**

---

## 🧠 Concept Overview

An ayah can be long and complex. Different translators may:

- Break it into different logical segments
- Phrase meanings differently
- Emphasize different parts

Bayaan handles this by:

- Dividing ayahs into **segments based on translation**
- Mapping each segment to a **range of Arabic words**
- Rendering both together in a visually aligned way

---

## 🏗️ Data Model (Final Design)

### 🔑 Key Decision

> We use **word-based segmentation**, NOT character-based.

Why?

- Arabic text includes diacritics and complex Unicode
- Character indexing is unreliable
- Word indexing is deterministic and stable

---

## 📦 Database Schema

### 1. `surahs`

Stores metadata about each Surah.

| Column         | Type        |
|----------------|------------|
| id             | INT (PK)   |
| name_arabic    | VARCHAR    |
| name_english   | VARCHAR    |

---

### 2. `ayahs`

Represents each ayah.

| Column        | Type        |
|--------------|------------|
| id           | INT (PK)   |
| surah_id     | INT (FK)   |
| ayah_number  | INT        |

---

### 3. `ayah_words` ⭐

Core table containing tokenized Quran text.

| Column        | Type        | Description |
|--------------|------------|------------|
| id           | BIGINT (PK)|
| surah_id     | INT        |
| ayah_number  | INT        |
| word_index   | INT        | Position in ayah |
| location     | VARCHAR    | e.g. "2:177:5" |
| text         | TEXT       | Arabic word |
| is_symbol    | BOOLEAN    | Marks sajdah/waqf symbols |

---

### 4. `translations`

Stores translation metadata.

| Column      | Type        |
|------------|------------|
| id         | INT (PK)   |
| name       | VARCHAR    |
| language   | VARCHAR    |
| direction  | ENUM       |

---

### 5. `translation_segments` ⭐ (Core Logic)

Defines how each translation segments an ayah.

| Column           | Type        | Description |
|------------------|------------|------------|
| id               | BIGINT (PK)|
| surah_id         | INT        |
| ayah_number      | INT        |
| translation_id   | INT (FK)   |
| segment_index    | INT        | Order of segment |
| word_start       | INT        | Start word index |
| word_end         | INT        | End word index |
| translation_text | TEXT       | Segment translation |

---

## 🔄 How It Works

### Step 1: Fetch Data

For a selected ayah and translation:

- Retrieve all `ayah_words`
- Retrieve corresponding `translation_segments`

---

### Step 2: Map Words to Segments

Each word belongs to a segment based on:
