import firebase_admin
from firebase_admin import credentials, auth, firestore
from datetime import datetime
import os

def _init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        firebase_admin.initialize_app(cred)

_init_firebase()
db = firestore.client()


def verify_id_token(token: str) -> dict:
    return auth.verify_id_token(token)


def get_user(uid: str):
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None


def create_user(uid: str, email: str, name: str, photo: str) -> dict:
    user = {
        "email": email,
        "name": name,
        "photoURL": photo,
        "plan": "free",
        "scansUsed": 0,
    }
    db.collection("users").document(uid).set({**user, "createdAt": firestore.SERVER_TIMESTAMP})
    return user


SCAN_FIELDS = (
    "ats_score", "hire_probability", "score_breakdown", "matched_keywords", "missing_keywords",
    "match_percentage", "bullet_analysis", "weak_bullets", "improved_bullets", "experience_years",
    "experience_periods", "required_years", "overall_feedback",
)


def save_scan(uid: str, scan_data: dict) -> str:
    doc = {k: scan_data.get(k) for k in SCAN_FIELDS if k in scan_data}
    _, ref = db.collection("scans").add({
        **doc,
        "userId": uid,
        "jobTitle": scan_data.get("job_title", ""),
        "createdAt": firestore.SERVER_TIMESTAMP,
    })
    return ref.id


def increment_scan_count(uid: str):
    db.collection("users").document(uid).update({
        "scansUsed": firestore.Increment(1)
    })


def get_user_scans(uid: str, limit: int = 50):
    docs = (
        db.collection("scans")
        .where("userId", "==", uid)
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [{"id": d.id, **d.to_dict()} for d in docs]
