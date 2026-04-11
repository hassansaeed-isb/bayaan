import json
import mysql.connector

# DB connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="bayaan",
    port=3212
)

cursor = conn.cursor()

# Load JSON
with open("indopak-nastaleeq.json", "r", encoding="utf-8") as f:
    data = json.load(f)

ayah_set = set()

for key, value in data.items():
    surah = int(value["surah"])
    ayah = int(value["ayah"])
    word_index = int(value["word"])
    location = value["location"]
    text = value["text"]
    word_id = int(value["id"])

    # Insert into ayahs (avoid duplicates)
    if (surah, ayah) not in ayah_set:
        cursor.execute("""
            INSERT IGNORE INTO ayahs (surah_id, ayah_number)
            VALUES (%s, %s)
        """, (surah, ayah))
        ayah_set.add((surah, ayah))

    # Detect symbols (basic heuristic)
    is_symbol = 1 if len(text.strip()) <= 2 else 0

    # Insert word
    cursor.execute("""
        INSERT INTO ayah_words (
            id, surah_id, ayah_number, word_index, location, text, is_symbol
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (word_id, surah, ayah, word_index, location, text, is_symbol))

# Commit
conn.commit()

cursor.close()
conn.close()

print("Import completed successfully.")