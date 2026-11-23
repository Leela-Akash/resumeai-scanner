"""Test setup: replace the Firebase module with an in-memory fake so tests never touch
real credentials or Firestore."""
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("GROQ_API_KEY", "test-key")


class FakeStore:
    def __init__(self):
        self.users: dict[str, dict] = {}
        self.scans: list[dict] = []

    def reset(self):
        self.users.clear()
        self.scans.clear()


STORE = FakeStore()

fake = types.ModuleType("services.firebase_service")
fake.verify_id_token = lambda token: {"uid": token, "email": f"{token}@example.com"} if token.startswith("user") else (_ for _ in ()).throw(ValueError("bad token"))
fake.get_user = lambda uid: STORE.users.get(uid)


def _create_user(uid, email, name, photo):
    STORE.users[uid] = {"email": email, "name": name, "photoURL": photo, "plan": "free", "scansUsed": 0}
    return STORE.users[uid]


def _save_scan(uid, data):
    STORE.scans.append({"userId": uid, **data})
    return f"scan{len(STORE.scans)}"


def _increment(uid):
    STORE.users[uid]["scansUsed"] += 1


fake.create_user = _create_user
fake.save_scan = _save_scan
fake.increment_scan_count = _increment
fake.get_user_scans = lambda uid, limit=50: [s for s in STORE.scans if s["userId"] == uid][:limit]
sys.modules["services.firebase_service"] = fake


@pytest.fixture
def store():
    STORE.reset()
    return STORE
