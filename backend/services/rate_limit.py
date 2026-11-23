from fastapi import Request
from slowapi import Limiter


def client_ip(request: Request) -> str:
    """Real client IP behind Render's proxy. Without this every user shares one rate-limit bucket
    (the proxy's IP), so one heavy user could lock everyone out."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip)
