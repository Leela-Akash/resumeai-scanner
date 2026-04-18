import os
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.pdf_service import extract_text_with_sections
from services.grok_service import (
    extract_resume_data,
    extract_jd_data,
    generate_bullet_improvements,
    generate_overall_feedback,
)
from services.analysis_service import (
    calculate_ats_score,
    calculate_experience_years,
    analyze_bullet,
    build_score_card,
    generate_quick_wins,
)
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
        resume_text, sections = extract_text_with_sections(file_bytes)
    except Exception:
        raise HTTPException(status_code=422, detail="Could not extract text from PDF")

    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="PDF appears to be empty or image-only")
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured")

    try:
        # Stage 1 & 2: parallel extraction
        import asyncio
        resume_data, jd_data = await asyncio.gather(
            extract_resume_data(resume_text, api_key),
            extract_jd_data(job_description, api_key),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI extraction failed: {str(e)}")

    # Stage 3: deterministic scoring (no AI)
    ats_score, breakdown = calculate_ats_score(resume_data, jd_data, resume_text)

    # Experience
    resume_years = resume_data.get("total_experience") or calculate_experience_years(resume_text)
    required_years = jd_data.get("required_years") or 0

    # Bullet analysis
    all_bullets = []
    for section in ["key_responsibilities"]:
        pass  # responsibilities are from JD, not resume

    # Extract bullets from resume text (lines starting with action indicators)
    import re
    bullet_lines = [
        line.strip("•·-– ").strip()
        for line in resume_text.splitlines()
        if len(line.strip()) > 20 and re.match(r'^[•·\-–*]|^\w+ed\s|^\w+ed,', line.strip())
    ][:15]

    bullet_analysis = [analyze_bullet(b) for b in bullet_lines]

    # Weak bullets for AI improvement
    weak_bullets = [b for b in bullet_analysis if b["grade"] in ("C", "D")][:5]

    try:
        improved, (overall_feedback, hire_probability) = await asyncio.gather(
            generate_bullet_improvements(weak_bullets, jd_data.get("job_title", ""), api_key),
            generate_overall_feedback(ats_score, resume_data, jd_data, breakdown, api_key),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI feedback failed: {str(e)}")

    # Attach improved versions to weak bullets
    for i, b in enumerate(weak_bullets):
        b["improved"] = improved[i] if i < len(improved) else ""

    # Skills lists
    resume_skills = (
        resume_data.get("technical_skills", []) +
        resume_data.get("programming_languages", []) +
        resume_data.get("frameworks", []) +
        resume_data.get("tools", [])
    )
    required_skills = jd_data.get("required_skills", [])

    from services.analysis_service import find_fuzzy_match
    matched_keywords = [s for s in required_skills if find_fuzzy_match(s, resume_skills)]
    missing_keywords = [s for s in required_skills if not find_fuzzy_match(s, resume_skills)]

    score_card = build_score_card(breakdown, sections, resume_years, required_years)
    quick_wins = generate_quick_wins(missing_keywords, sections, bullet_analysis)

    seniority = jd_data.get("seniority_level", "mid") or "mid"
    seniority_match = (
        "Strong fit" if ats_score >= 75
        else "Good fit" if ats_score >= 55
        else "Partial fit" if ats_score >= 35
        else "Weak fit"
    )

    result = {
        "ats_score": ats_score,
        "score_breakdown": breakdown,
        "job_title": jd_data.get("job_title", ""),
        "seniority_match": seniority_match,
        "experience_years": {
            "resume_has": resume_years,
            "job_requires": required_years,
            "match": resume_years >= required_years,
        },
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "preferred_keywords_missing": [
            s for s in jd_data.get("preferred_skills", [])
            if not find_fuzzy_match(s, resume_skills)
        ],
        "resume_sections": sections,
        "bullet_analysis": bullet_analysis,
        "overall_feedback": overall_feedback,
        "hire_probability": hire_probability,
        "quick_wins": quick_wins,
        "resume_score_card": score_card,
    }

    uid = user["uid"]
    save_scan(uid, result)
    increment_scan_count(uid)

    return result
