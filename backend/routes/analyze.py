from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.pdf_service import extract_text
from services.grok_service import call_grok
from services.firebase_service import save_scan, increment_scan_count
from middleware.check_subscription import check_subscription

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/analyze")
@limiter.limit("10/minute")
async def analyze(
    request: Request,
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    user: dict = Depends(check_subscription),
):
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    file_bytes = await resume.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF must be under 5MB")

    try:
        resume_text = extract_text(file_bytes)
    except Exception:
        raise HTTPException(status_code=422, detail="Could not extract text from PDF")

    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="PDF appears to be empty or image-only")
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    try:
        result = await call_grok(resume_text, job_description)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {str(e)}")

    uid = user["uid"]
    save_scan(uid, result)
    increment_scan_count(uid)

    return result
