import sqlite3

import pytest

from attendance_camera.store import Store


def test_persistence_correction_and_aggregate_only_storage(tmp_path):
    path = tmp_path / "counts.sqlite3"
    store = Store(path)
    session = store.start(10)
    store.record(3, 1)
    assert store.active()["occupancy"] == 12
    store.reconcile(11)
    store.record(1, 0)
    assert store.active()["occupancy"] == 12
    rows = store.minutes(session["id"])
    assert len(rows) == 1 and rows[0]["incoming"] == 4 and rows[0]["correction"] == -1
    store.close()
    restored = Store(path)
    assert restored.active()["occupancy"] == 12
    restored.end()
    assert restored.active() is None
    assert restored.sessions()[0]["ended_at"] is not None
    restored.close()
    db = sqlite3.connect(path)
    columns = [row[1] for row in db.execute("PRAGMA table_info(minutes)")]
    assert columns == ["session_id", "minute", "incoming", "outgoing", "correction", "occupancy"]
    db.close()


def test_negative_balance_is_visible_and_requires_reconciliation(tmp_path):
    store = Store(tmp_path / "counts.sqlite3")
    store.start(0)
    store.record(0, 2)
    assert store.active()["occupancy"] == 0
    assert store.active()["net_count"] == -2
    assert store.active()["needs_reconciliation"]
    store.reconcile(5)
    assert store.active()["occupancy"] == 5
    assert not store.active()["needs_reconciliation"]
    store.close()


def test_only_one_active_session_and_one_server(tmp_path):
    path = tmp_path / "counts.sqlite3"
    store = Store(path)
    with pytest.raises(RuntimeError):
        Store(path)
    store.start(0)
    with pytest.raises(ValueError):
        store.start(1)
    store.close()
