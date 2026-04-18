from fastapi import APIRouter, Depends
from middleware.verify_token import verify_token
from services.firebase_service import get_user_scans

router = APIRouter()


@router.get("/history")
def history(decoded: dict = Depends(verify_token)):
    uid = decoded["uid"]
    scans = get_user_scans(uid)
    # Convert Firestore timestamps to ISO strings for JSON serialization
    for scan in scans:
        if "createdAt" in scan and hasattr(scan["createdAt"], "isoformat"):
            scan["createdAt"] = scan["createdAt"].isoformat()
    return scans
