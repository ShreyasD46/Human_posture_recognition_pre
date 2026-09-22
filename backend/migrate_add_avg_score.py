"""
One-time migration script: add the avg_score column to the session table.
Run once from the backend/ directory:

    python migrate_add_avg_score.py

Safe to run multiple times — checks if the column already exists first.
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "yoga.db")


def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check existing columns
    cur.execute("PRAGMA table_info(session)")
    existing = {row[1] for row in cur.fetchall()}

    if "avg_score" not in existing:
        cur.execute("ALTER TABLE session ADD COLUMN avg_score REAL DEFAULT 0")
        conn.commit()
        print("[OK] Added avg_score column to session table.")
    else:
        print("[INFO] avg_score column already exists -- nothing to do.")

    conn.close()


if __name__ == "__main__":
    run()
