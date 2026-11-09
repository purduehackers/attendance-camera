"""SQLite stores aggregate counts and configuration, never frames or track IDs."""

import json
import fcntl
from pathlib import Path
import sqlite3
import threading
import time
import uuid


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.owner = open(str(path) + ".lock", "a")
        try:
            fcntl.flock(self.owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.owner.close()
            raise RuntimeError("This database already has a running attendance server.") from None
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, started_at REAL NOT NULL, ended_at REAL,
                baseline INTEGER NOT NULL, incoming INTEGER NOT NULL DEFAULT 0,
                outgoing INTEGER NOT NULL DEFAULT 0, correction INTEGER NOT NULL DEFAULT 0,
                needs_reconciliation INTEGER NOT NULL DEFAULT 1
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_active ON sessions((1)) WHERE ended_at IS NULL;
            CREATE TABLE IF NOT EXISTS minutes (
                session_id TEXT REFERENCES sessions(id), minute INTEGER,
                incoming INTEGER NOT NULL DEFAULT 0, outgoing INTEGER NOT NULL DEFAULT 0,
                correction INTEGER NOT NULL DEFAULT 0, occupancy INTEGER NOT NULL,
                PRIMARY KEY(session_id, minute)
            );
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        path.chmod(0o600)

    def close(self):
        self.db.close()
        self.owner.close()

    def active(self):
        with self.lock:
            row = self.db.execute("SELECT * FROM sessions WHERE ended_at IS NULL").fetchone()
            return self._session(row) if row else None

    @staticmethod
    def _session(row):
        result = dict(row)
        raw = result["baseline"] + result["incoming"] - result["outgoing"] + result["correction"]
        result.update(
            net_count=raw,
            occupancy=max(0, raw),
            needs_reconciliation=bool(result["needs_reconciliation"] or raw < 0),
        )
        return result

    def start(self, baseline: int):
        with self.lock, self.db:
            if self.active():
                raise ValueError("End the current session before starting another.")
            self.db.execute(
                "INSERT INTO sessions(id,started_at,baseline,needs_reconciliation) VALUES(?,?,?,0)",
                (str(uuid.uuid4()), time.time(), baseline),
            )
            return self.active()

    def end(self):
        with self.lock, self.db:
            self.db.execute("UPDATE sessions SET ended_at=? WHERE ended_at IS NULL", (time.time(),))

    def reconcile(self, occupancy: int):
        with self.lock, self.db:
            session = self.active()
            if not session:
                raise ValueError("Start a session first.")
            correction = occupancy - session["net_count"]
            self.db.execute(
                "UPDATE sessions SET correction=correction+?,needs_reconciliation=0 WHERE id=?",
                (correction, session["id"]),
            )
            self._minute(session["id"], 0, 0, correction)
            return self.active()

    def mark_gap(self):
        with self.lock, self.db:
            self.db.execute("UPDATE sessions SET needs_reconciliation=1 WHERE ended_at IS NULL")

    def record(self, incoming: int, outgoing: int):
        if not (incoming or outgoing):
            return
        with self.lock, self.db:
            session = self.active()
            if not session:
                return
            self.db.execute(
                "UPDATE sessions SET incoming=incoming+?,outgoing=outgoing+? WHERE id=?",
                (incoming, outgoing, session["id"]),
            )
            if self.active()["net_count"] < 0:
                self.db.execute(
                    "UPDATE sessions SET needs_reconciliation=1 WHERE id=?", (session["id"],)
                )
            self._minute(session["id"], incoming, outgoing, 0)

    def _minute(self, session_id, incoming, outgoing, correction):
        self.db.execute(
            """INSERT INTO minutes VALUES(?,?,?,?,?,?)
            ON CONFLICT(session_id,minute) DO UPDATE SET
            incoming=incoming+excluded.incoming, outgoing=outgoing+excluded.outgoing,
            correction=correction+excluded.correction, occupancy=excluded.occupancy""",
            (
                session_id,
                int(time.time() // 60) * 60,
                incoming,
                outgoing,
                correction,
                self.active()["occupancy"],
            ),
        )

    def sessions(self):
        with self.lock:
            return [
                self._session(row)
                for row in self.db.execute(
                    "SELECT * FROM sessions ORDER BY started_at DESC LIMIT 100"
                )
            ]

    def minutes(self, session_id: str):
        with self.lock:
            return [
                dict(row)
                for row in self.db.execute(
                    "SELECT * FROM minutes WHERE session_id=? ORDER BY minute", (session_id,)
                )
            ]

    def get_setting(self, key):
        with self.lock:
            row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return json.loads(row[0]) if row else None

    def set_setting(self, key, value):
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value)),
            )
