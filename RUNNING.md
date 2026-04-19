# Bayaan — run the API (minimal)

**What you get:** a small **FastAPI** service that reads the Qur’an **word list** and **translation segments** from **MySQL**. The app does **not** read the `bayan ul quran` folder at request time; that content is **imported in batch** into the database.

| Piece | Role |
|--------|------|
| `app/app.py` | HTTP: `GET /ayah/...`, `GET/POST /segments/...` |
| `data/import-quran-aya-words.py` | Fills `ayah_words` (Quran.com API or legacy JSON) |
| `scripts/import_bayan_segments.py` / `batch_import_bayan.py` | Fills `translation_segments` from Bayan exports |
| `data/db-schema.sql` | Schema + surah list + default `translations` row |
| `bayan ul quran/` | **Source files** for imports only (not used live by the API) |

Deeper product + data model: [ReadMe.md](ReadMe.md), [TechnicalOverview.md](TechnicalOverview.md).

---

## 1) MySQL (pick one)

### A — Docker (port on localhost)

```bash
docker compose up -d
```

Copy `app/.env.example` → `app/.env` and set (match your compose password / port):

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=bayaan_dev
DB_NAME=bayaan
```

`data/db-schema.sql` is applied **automatically the first time** the MySQL data volume is created. If you change the SQL and need a clean DB: `docker compose down -v` then `docker compose up -d`.

Override port mapping, e.g. host `3307` → container `3306`:

```bash
set MYSQL_PORT=3307
docker compose up -d
```

…then set `DB_PORT=3307` in `app/.env`.

### B — MySQL you already run

Point `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` in `app/.env` at that instance, then apply schema (MySQL client or `python scripts/apply_schema.py` with `app/.env` filled in).

---

## 2) Python

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

---

## 3) Data (optional but needed for non-empty API)

```bash
# Arabic words (all surahs) — needs network for API mode
python data/import-quran-aya-words.py --all-chapters

# Or from a local flat JSON (same fields as before)
# python data/import-quran-aya-words.py --legacy-json data/indopak-nastaleeq.json/indopak-nastaleeq.json

# Bayan Urdu segments from exports under `bayan ul quran/`
python scripts/batch_import_bayan.py --skip-unknown
```

---

## 4) Start API

```bash
python -m uvicorn app.app:app --host 127.0.0.1 --port 8001 --reload
```

Open **http://127.0.0.1:8001/docs** — try `GET /ayah/2/1` and `GET /segments/1/2/1` (`translation_id` **1** is seeded as bayan-ul-quran).

If Windows blocks port **8000**, use **8001** (or another free port).

---

## Environment reference

| Variable | Typical |
|----------|---------|
| `DB_HOST` | `127.0.0.1` (Docker with published port) or remote host |
| `DB_PORT` | `3306` or mapped host port |
| `DB_USER` / `DB_PASSWORD` / `DB_NAME` | match MySQL |

Configuration is loaded from `app/.env` and the repo root `.env` (see `app/config.py`).

---

## Commit snapshot — “what runs how”

| Area | What happens |
|------|----------------|
| Runtime | **FastAPI** queries MySQL only (`ayah_words`, `translation_segments`, …). |
| Imports | **Scripts** pull Quran words (API/JSON) and Bayan text (folder exports) **into** MySQL **once per job**. |
| `bayan ul quran/` | Stays on disk as **source**; not read by the live API. |
| Docker | `docker-compose.yml` runs **MySQL 8** and auto-seeds from `data/db-schema.sql` on first volume create. |
