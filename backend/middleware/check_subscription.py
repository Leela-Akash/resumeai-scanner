import os

from fastapi import Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from middleware.verify_token import verify_token
from services.firebase_service import create_user, get_user


def free_scan_limit() -> int:
    """Scans allowed on the free plan. 0 (default) means unlimited.
    Set FREE_SCAN_LIMIT=3 once a paid plan exists for users to upgrade to."""
    try:
        return max(0, int(os.getenv("FREE_SCAN_LIMIT", "0")))
    except ValueError:
        return 0


async def check_subscription(decoded: dict = Depends(verify_token)) -> dict:
    uid = decoded["uid"]
    user = await run_in_threadpool(get_user, uid)
    if not user:
        user = await run_in_threadpool(
            create_user,
            uid,
            decoded.get("email", ""),
            decoded.get("name", ""),
            decoded.get("picture", ""),
        )

    limit = free_scan_limit()
    if user.get("plan", "free") == "free" and limit and user.get("scansUsed", 0) >= limit:
        # The frontend listens for this exact detail string.
        raise HTTPException(status_code=403, detail="FREE_LIMIT_REACHED")

    return {**user, "uid": uid}
