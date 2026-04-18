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


def create_user(uid: str, email: str, name: str, photo: str):
    db.collection("users").document(uid).set({
        "email": email,
        "name": name,
        "photoURL": photo,
        "plan": "free",
        "scansUsed": 0,
        "scansLimit": 3,
        "createdAt": firestore.SERVER_TIMESTAMP,
    })


def save_scan(uid: str, scan_data: dict):
    ref = db.collection("scans").add({
        "userId": uid,
        "jobTitle": scan_data.get("job_title", ""),
        "ats_score": scan_data.get("ats_score"),
        "score_breakdown": scan_data.get("score_breakdown", {}),
        "matched_keywords": scan_data.get("matched_keywords", []),
        "missing_keywords": scan_data.get("missing_keywords", []),
        "preferred_keywords_missing": scan_data.get("preferred_keywords_missing", []),
        "bullet_analysis": scan_data.get("bullet_analysis", []),
        "resume_sections": scan_data.get("resume_sections", {}),
        "overall_feedback": scan_data.get("overall_feedback", ""),
        "hire_probability": scan_data.get("hire_probability", ""),
        "seniority_match": scan_data.get("seniority_match", ""),
        "experience_years": scan_data.get("experience_years", {}),
        "quick_wins": scan_data.get("quick_wins", []),
        "resume_score_card": scan_data.get("resume_score_card", {}),
        "createdAt": firestore.SERVER_TIMESTAMP,
    })
    return ref[1].id


def increment_scan_count(uid: str):
    db.collection("users").document(uid).update({
        "scansUsed": firestore.Increment(1)
    })


def get_user_scans(uid: str):
    docs = (
        db.collection("scans")
        .where("userId", "==", uid)
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .stream()
    )
    return [{"id": d.id, **d.to_dict()} for d in docs]
