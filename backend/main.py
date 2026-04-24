from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from datetime import datetime
import logging
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase on startup
import services.firebase_service  # noqa: F401

from routes.analyze import router as analyze_router
from routes.history import router as history_router

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="ResumeAI Scanner API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://getshortlisted.me",
        "https://www.getshortlisted.me",
        "https://leela-akash.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )


app.include_router(analyze_router, prefix="/api")
app.include_router(history_router, prefix="/api")


@app.get("/health")
async def health():
    groq_status = "up" if os.getenv("GROQ_API_KEY") else "missing_key"
    firebase_status = "up" if os.getenv("FIREBASE_PROJECT_ID") else "missing_key"
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "groq": groq_status,
            "firebase": firebase_status,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
