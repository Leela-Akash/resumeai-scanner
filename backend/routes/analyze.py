import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool

from middleware.check_subscription import check_subscription
from services.firebase_service import increment_scan_count, save_scan
from services.grok_service import analyze_resume
from services.llm import LLMError
from services.pdf_service import PDFError, extract_text
from services.rate_limit import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_PDF_BYTES = 5 * 1024 * 1024
MIN_JD_CHARS = 50
MAX_JD_CHARS = 8_000


@router.post("/analyze")
@limiter.limit("10/minute")
async def analyze(
    request: Request,
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    user: dict = Depends(check_subscription),
):
    jd = job_description.strip()
    if len(jd) < MIN_JD_CHARS:
        raise HTTPException(400, "Paste the full job description (at least a few sentences).")
    if len(jd) > MAX_JD_CHARS:
        raise HTTPException(400, f"Job description is too long (max {MAX_JD_CHARS:,} characters).")

    file_bytes = await resume.read(MAX_PDF_BYTES + 1)
    if len(file_bytes) > MAX_PDF_BYTES:
        raise HTTPException(413, "PDF must be under 5MB.")
    # Check the file itself, not just the client-supplied content type.
    if not file_bytes.startswith(b"%PDF"):
        raise HTTPException(400, "Only PDF files are accepted.")

    try:
        resume_text = await run_in_threadpool(extract_text, file_bytes)
    except PDFError as e:
        raise HTTPException(422, str(e))

    try:
        result = await analyze_resume(resume_text, jd)
    except LLMError as e:
        logger.error("Analysis failed for uid=%s: %s", user["uid"], e)
        raise HTTPException(503, "The AI service is busy right now. Please try again in a minute.")

    uid = user["uid"]
    try:
        result["id"] = await run_in_threadpool(save_scan, uid, result)
        await run_in_threadpool(increment_scan_count, uid)
    except Exception:
        # The user still gets their result if history saving fails.
        logger.exception("Failed to save scan for uid=%s", uid)

    return result
