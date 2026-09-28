import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


SCHEMA = """
CREATE TABLE IF NOT EXISTS classes (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('teacher', 'student')),
  class_id TEXT NOT NULL REFERENCES classes(id)
);
CREATE TABLE IF NOT EXISTS materials (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  class_id TEXT NOT NULL REFERENCES classes(id),
  uploader_id INTEGER NOT NULL REFERENCES users(id),
  title TEXT NOT NULL,
  filename TEXT NOT NULL,
  storage_name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS knowledge_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  class_id TEXT NOT NULL REFERENCES classes(id),
  material_id INTEGER NOT NULL REFERENCES materials(id),
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db():
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        seed_passwords = (
            current_app.config.get("SEED_TEACHER_PASSWORD"),
            current_app.config.get("SEED_STUDENT_A_PASSWORD"),
            current_app.config.get("SEED_STUDENT_B_PASSWORD"),
        )
        if not all(seed_passwords):
            raise RuntimeError("Seed user passwords must be configured before first startup")
        db.executemany("INSERT INTO classes (id, name) VALUES (?, ?)", [("A", "高一（A）班"), ("B", "高一（B）班")])
        users = [
            ("teacher_a", generate_password_hash(seed_passwords[0]), "teacher", "A"),
            ("student_a1", generate_password_hash(seed_passwords[1]), "student", "A"),
            ("student_b1", generate_password_hash(seed_passwords[2]), "student", "B"),
        ]
        db.executemany("INSERT INTO users (username, password_hash, role, class_id) VALUES (?, ?, ?, ?)", users)
        teacher_id = db.execute("SELECT id FROM users WHERE username = 'teacher_a'").fetchone()[0]
        samples = [
            ("A", teacher_id, "A班教研入门材料", "a-intro.md", "a-intro.md"),
        ]
        db.executemany("INSERT INTO materials (class_id, uploader_id, title, filename, storage_name) VALUES (?, ?, ?, ?, ?)", samples)
        material_id = db.execute("SELECT id FROM materials WHERE filename = 'a-intro.md'").fetchone()[0]
        db.execute("INSERT INTO knowledge_entries (class_id, material_id, content) VALUES ('A', ?, ?)", (material_id, "A班专属教研材料：课堂观察与反馈。"))
        db.commit()
    Path(current_app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
