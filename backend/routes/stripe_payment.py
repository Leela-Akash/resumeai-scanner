import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from middleware.verify_token import verify_token
from services.firebase_service import update_user_plan

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PLAN_PRICE_MAP = {
    "pro": os.getenv("STRIPE_PRO_PRICE_ID"),
    "premium": os.getenv("STRIPE_PREMIUM_PRICE_ID"),
}


class CheckoutRequest(BaseModel):
    plan: str


@router.post("/create-checkout-session")
async def create_checkout_session(
    body: CheckoutRequest,
    decoded: dict = Depends(verify_token),
):
    price_id = PLAN_PRICE_MAP.get(body.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan")

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            metadata={"user_id": decoded["uid"], "plan": body.plan},
            success_url=f"{frontend_url}/success",
            cancel_url=f"{frontend_url}/pricing",
        )
    except stripe.StripeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {"url": session.url}


@router.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        uid = session.get("metadata", {}).get("user_id")
        plan = session.get("metadata", {}).get("plan", "pro")
        if uid:
            update_user_plan(uid, plan)

    return {"status": "ok"}
