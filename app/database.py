import sqlite3
from contextlib import contextmanager

DB_PATH = "data/fingerprints.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS songs (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    title    TEXT NOT NULL,
    artist   TEXT NOT NULL,
    duration REAL
);

CREATE TABLE IF NOT EXISTS fingerprints (
    hash        TEXT NOT NULL,
    song_id     INTEGER NOT NULL,
    time_offset INTEGER NOT NULL,
    FOREIGN KEY (song_id) REFERENCES songs(id)
);

CREATE INDEX IF NOT EXISTS idx_hash ON fingerprints(hash);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def insert_song(title: str, artist: str, duration: float) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO songs (title, artist, duration) VALUES (?,?,?)",
            (title, artist, duration)
        )
        return cur.lastrowid


def insert_fingerprints(song_id: int, hashes: list[tuple[str, int]]):
    with get_conn() as conn:
        conn.execute("BEGIN TRANSACTION")
        conn.executemany(
            "INSERT INTO fingerprints (hash, song_id, time_offset) VALUES (?,?,?)",
            [(h, song_id, t) for h, t in hashes]
        )
        conn.execute("COMMIT")


def query_hashes(hashes: list[str]) -> list[tuple[str, int, int]]:
    """Returns (hash, song_id, time_offset) for all matching hashes."""
    rows = []
    with get_conn() as conn:
        for i in range(0, len(hashes), 999):
            chunk = hashes[i:i + 999]
            placeholders = ",".join("?" * len(chunk))
            rows += conn.execute(
                f"SELECT hash, song_id, time_offset FROM fingerprints WHERE hash IN ({placeholders})",
                chunk
            ).fetchall()
    return rows
