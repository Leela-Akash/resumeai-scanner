import hmac
import hashlib
import os
from fastapi import APIRouter, Request, HTTPException

from services.firebase_service import update_user_plan

router = APIRouter()

PLAN_MAP = {
    "pro": "pro",
    "premium": "premium",
}


@router.post("/payment/webhook")
async def payment_webhook(request: Request):
    secret = os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "")
    body = await request.body()

    signature = request.headers.get("X-Signature", "")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("meta", {}).get("event_name", "")

    if event == "order_created":
        custom_data = payload.get("meta", {}).get("custom_data", {})
        uid = custom_data.get("user_id")
        plan = custom_data.get("plan", "pro")

        if not uid:
            raise HTTPException(status_code=400, detail="Missing user_id in custom_data")

        update_user_plan(uid, PLAN_MAP.get(plan, "pro"))

    return {"status": "ok"}
