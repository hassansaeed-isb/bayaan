# Bayaan — Technical Overview & Architecture

This document explains the **technical architecture, design decisions, and core challenges** behind Bayaan.

It is intended for developers working on the system or extending it.

---

## 🧠 Problem Definition

Bayaan is not a typical text-rendering application.

It solves a **text alignment problem**, specifically:

> Mapping semantically segmented translation units to precise positions within a structured source text (Qur’anic Arabic), and rendering them in a responsive UI.

---

## 🔬 Closest Existing Domains

Bayaan’s architecture overlaps with:

### 1. Bilingual Text Alignment Systems
- Used in translation research
- Aligns source and target language segments
- Usually sentence-based or phrase-based

**Difference:**
- Bayaan requires **manual, semantic segmentation**
- Not automatic or statistical alignment

---

### 2. Linguistic Annotation Tools
Examples:
- Treebanks
- Corpus annotation systems

**Similarity:**
- Text is tokenized (word-level)
- Metadata is attached to spans

**Difference:**
- Bayaan focuses on **UI rendering alignment**, not just annotation

---

### 3. Interlinear Scripture Systems
- Used in Bible study tools

**Similarity:**
- Mapping between source and translation

**Difference:**
- Bayaan allows **variable segmentation per translation**
- Not strictly word-to-word mapping

---

## 🏗️ Core Architectural Decision

### ❗ Word-Based Segmentation (Critical)

We explicitly **do NOT use character-based indexing**.

### Why character-based fails:

- Arabic includes:
  - Diacritics (harakat)
  - Ligatures
  - Unicode normalization issues
- Same visible text can have multiple underlying representations
- Substring matching becomes unreliable

---

### ✅ Word-Based Model

Each ayah is tokenized into:
surah : ayah : word_index
Example:

4:1:1 → یٰۤاَیُّهَا
4:1:2 → النَّاسُ


---

### Advantages:

- Deterministic indexing
- Stable across systems
- Easy segmentation
- Perfect for highlighting
- Avoids Unicode pitfalls

---

## 📦 Data Model Philosophy

### Separation of Concerns

| Concept | Stored Where |
|--------|-------------|
| Arabic text | `ayah_words` |
| Translation metadata | `translations` |
| Segmentation logic | `translation_segments` |

---

### Key Insight

> **Segmentation is translation-dependent, not ayah-dependent**

This is fundamental.

---

## 🔀 Segmentation Model

Each translation defines its own segmentation:

Ayah → [Segment 1, Segment 2, Segment 3...]


Each segment maps to:
[word_start, word_end]


---

### Implications

- Same ayah can have:
  - 2 segments in Urdu translation A
  - 3 segments in Urdu translation B
- No conflict in schema
- Fully flexible

---

## 🎨 Rendering Challenges

This is the most complex part of the system.

---

### 1. Alignment Problem

Goal:

> Translation must appear directly under the corresponding Arabic segment

---

### Problem:

- Arabic and Urdu lengths differ
- Line wrapping is unpredictable
- Fonts render differently
- Browser layout engines are not alignment-aware

---

### Solution Strategy (Current)

Use **block-based rendering**:

[Arabic segment]
[Translation segment]


---

### Alternative (Future)

Inline alignment:

Arabic flowing text
Translation aligned beneath exact spans


---

### Why it's hard:

- Requires measuring rendered text width
- Requires layout synchronization
- Becomes a custom layout engine problem

---

## ↔️ RTL / LTR Complexity

### Current Scope:

- Arabic (RTL)
- Urdu (RTL)

---

### Future Challenge:

Supporting:
- English (LTR)
- Mixed-direction layouts

---

### Problems:

- Direction switching
- Text alignment inconsistencies
- CSS `direction` and `unicode-bidi` quirks
- Inline vs block rendering conflicts

---

### Example Challenge

Arabic (RTL) + English (LTR):

[Arabic segment →]
[← English translation]


Maintaining visual alignment is non-trivial.

---

## 🎯 Highlighting System Challenges

Bayaan aims to support:

- Segment highlighting
- Word-level highlighting (future)
- Teaching mode

---

### Problems:

1. Mapping hover/click to segment
2. Maintaining highlight across wrapped lines
3. Synchronizing Arabic + translation highlight
4. Performance with many DOM nodes

---

### Why Word-Based Helps

- Each word is a discrete unit
- Easy to assign classes:
  
  seg-1, seg-2, seg-3

  
---

## ⚙️ Performance Considerations

### Potential Issues:

- Large DOM trees (many words)
- Frequent re-renders (React)
- Complex layout recalculations

---

### Mitigations:

- Memoization
- Virtualization (if needed)
- Segment-level rendering instead of word-level (when possible)

---

## 🧩 Data Entry Challenge (Major)

Segmentation is:

- Manual
- Subjective
- Translation-dependent

---

### Implication:

You will need:

- Admin UI OR
- Structured import system

---

### Example Format

```json id="d5u4lm"
{
  "2:177": [
    { "start": 1, "end": 10, "text": "..." },
    { "start": 11, "end": 25, "text": "..." }
  ]
}

🔮 Future Extensions
1. Word-Level Translation
Mapping each Arabic word to meaning
Requires additional tables
2. Audio Synchronization
Align audio timestamps with segments
3. Tafsir Integration
Attach commentary to segments
4. Advanced Layout Engine
Pixel-perfect alignment
Possibly canvas-based rendering
⚠️ Known Limitations
Perfect inline alignment is not solved initially
Manual segmentation is labor-intensive
Rendering complexity increases with features
🧭 Guiding Principles
Correctness over cleverness
Deterministic indexing (word-based)
Separation of data and rendering
Progressive enhancement (start simple, evolve)
📌 Summary

Bayaan is fundamentally:

A structured text alignment system built on top of a word-tokenized Qur’anic corpus.

Its complexity lies not in storage, but in:

Alignment modeling
Rendering logic
Multilingual layout handling

The decision to use word-based segmentation is central to making the system reliable, scalable, and maintainable.