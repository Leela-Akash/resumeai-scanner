from fastapi import Depends, HTTPException, status
from middleware.verify_token import verify_token
from services.firebase_service import get_user, create_user


def check_subscription(decoded: dict = Depends(verify_token)) -> dict:
    uid = decoded["uid"]
    user = get_user(uid)

    if not user:
        create_user(
            uid=uid,
            email=decoded.get("email", ""),
            name=decoded.get("name", ""),
            photo=decoded.get("picture", ""),
        )
        user = {"plan": "free", "scansUsed": 0, "scansLimit": 3}

    if user.get("plan", "free") == "free" and user.get("scansUsed", 0) >= 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FREE_LIMIT_REACHED",
        )

    return {**user, "uid": uid}
