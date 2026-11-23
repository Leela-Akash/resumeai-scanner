from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool

from middleware.verify_token import verify_token
from services.firebase_service import get_user_scans

router = APIRouter()


@router.get("/history")
async def history(
    limit: int = Query(50, ge=1, le=100),
    decoded: dict = Depends(verify_token),
):
    scans = await run_in_threadpool(get_user_scans, decoded["uid"], limit)
    for scan in scans:
        if hasattr(scan.get("createdAt"), "isoformat"):
            scan["createdAt"] = scan["createdAt"].isoformat()
    return scans
