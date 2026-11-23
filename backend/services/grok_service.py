"""Resume analysis pipeline.

  Stage 1  Keyword extraction (LLM, JD + resume in parallel) -> deterministic matching
  Stage 2  Bullet review (one batched LLM call: score + rewrite without invented numbers)
  Stage 3  Experience from the Experience section only (deterministic)
  Stage 4  ATS score (deterministic, weights below)
  Stage 5  Written feedback (LLM, optional: falls back to a template on failure)

Only stages 1 and 2 are required. If they fail the request fails with a clear error
rather than returning a made-up score.
"""
import asyncio
import logging
import re

from services.experience import calculate_experience, required_years
from services.llm import LLMError, complete_json, complete_text
from services.matching import match_keywords
from services.schemas import BulletBatch, KeywordSet

logger = logging.getLogger(__name__)

# Score weights (sum to 1.0)
W_KEYWORDS = 0.40
W_BULLETS = 0.30
W_EXPERIENCE = 0.20
W_FORMAT = 0.10

MAX_BULLETS = 8
MAX_RESUME_CHARS = 12_000
MAX_JD_CHARS = 8_000

_KEYWORD_SYSTEM = (
    "You extract skills for an applicant tracking system. Return a JSON object only. "
    "Use short canonical names (e.g. 'React', 'PostgreSQL', 'CI/CD'), no sentences, no duplicates."
)
_KEYWORD_SHAPE = (
    '{"technical_skills": [], "tools_frameworks": [], "soft_skills": [], "certifications": []}'
)


# ─────────────────────────────────────────────
# Stage 1: keywords
# ─────────────────────────────────────────────

async def extract_keywords(text: str, kind: str) -> KeywordSet:
    user = (
        f"Extract the skills from this {kind}. "
        + ("Include only skills the role actually asks for. " if kind == "job description" else "")
        + f"Return exactly this JSON shape: {_KEYWORD_SHAPE}\n\n{kind.upper()}:\n{text}"
    )
    return await complete_json(_KEYWORD_SYSTEM, user, KeywordSet, temperature=0.0)


async def keyword_stage(resume_text: str, jd_text: str) -> dict:
    jd, resume = await asyncio.gather(
        extract_keywords(jd_text, "job description"),
        extract_keywords(resume_text, "resume"),
    )
    result = match_keywords(jd.hard_skills(), resume.hard_skills(), resume_text)
    logger.info("Stage 1: %d matched, %d missing", len(result["matched_keywords"]), len(result["missing_keywords"]))
    return result


# ─────────────────────────────────────────────
# Stage 2: bullets
# ─────────────────────────────────────────────

_BULLET_START = re.compile(r"^[•·\-–*►▪▸○]+\s*")
_ACTION_START = re.compile(
    r"^(Led|Built|Designed|Developed|Implemented|Architected|Optimized|Deployed|Automated|"
    r"Managed|Created|Launched|Improved|Reduced|Increased|Delivered|Streamlined|Engineered|"
    r"Migrated|Integrated)\b"
)


def extract_bullets(resume_text: str) -> list[str]:
    bullets: list[str] = []
    for line in resume_text.splitlines():
        line = line.strip()
        if len(line) < 20:
            continue
        if _BULLET_START.match(line):
            cleaned = _BULLET_START.sub("", line).strip()
            if cleaned:
                bullets.append(cleaned)
        elif _ACTION_START.match(line):
            bullets.append(line)
    return list(dict.fromkeys(bullets))[:15]


_BULLET_SYSTEM = (
    "You are a strict but fair resume reviewer. Return a JSON object only. "
    "Never invent numbers, users, percentages or technologies the candidate did not mention. "
    "When a rewrite needs a metric the candidate didn't give, insert a placeholder like [X%] or [N users] "
    "so the candidate fills in the real value."
)


async def bullet_stage(resume_text: str, jd_keywords: list[str]) -> dict:
    bullets = extract_bullets(resume_text)[:MAX_BULLETS]
    if not bullets:
        return {"bullet_analysis": [], "average_score": None, "weak_bullets_count": 0}

    numbered = "\n".join(f"{i + 1}. {b}" for i, b in enumerate(bullets))
    user = f"""Review each resume bullet below. Score 0-10:
+3 has a concrete number or metric, +2 starts with a strong action verb,
+3 shows an outcome or impact, +2 uses skills relevant to the job ({', '.join(jd_keywords[:20]) or 'n/a'}).
Give partial credit. For bullets scoring below 6, write an improved version that keeps every fact
from the original and uses [placeholders] for missing metrics. Otherwise leave "improved" empty.

Return exactly {len(bullets)} reviews, in order:
{{"reviews": [{{"score": 0, "issues": ["short issue"], "improved": ""}}]}}

BULLETS:
{numbered}"""
    batch = await complete_json(_BULLET_SYSTEM, user, BulletBatch, temperature=0.1, max_tokens=2000)
    if len(batch.reviews) != len(bullets):
        raise LLMError(f"expected {len(bullets)} bullet reviews, got {len(batch.reviews)}")

    analysis = [
        {
            "original": b,
            "score": r.score,
            "issues": r.issues,
            "improved": r.improved if r.score < 6 else "",
        }
        for b, r in zip(bullets, batch.reviews)
    ]
    avg = round(sum(a["score"] for a in analysis) / len(analysis), 1)
    weak = sum(1 for a in analysis if a["score"] < 6)
    logger.info("Stage 2: avg %.1f, %d weak", avg, weak)
    return {"bullet_analysis": analysis, "average_score": avg, "weak_bullets_count": weak}


# ─────────────────────────────────────────────
# Stage 4: score
# ─────────────────────────────────────────────

def format_quality_score(resume_text: str) -> int:
    """0-100 for structure an ATS can parse: core sections, bullets, dates, contact info."""
    t = resume_text.lower()
    score = 0
    if re.search(r"\b(experience|work history|employment|internships?)\b", t):
        score += 20
    if re.search(r"\b(skills|technical skills|competencies)\b", t):
        score += 15
    if re.search(r"\b(education|university|college|b\.?tech|bachelor)\b", t):
        score += 15
    if re.search(r"\bprojects?\b", t):
        score += 10
    if len(re.findall(r"^[•·\-–*►▪▸○]", resume_text, re.MULTILINE)) >= 5:
        score += 20
    if len(re.findall(r"\b(19|20)\d{2}\b", resume_text)) >= 2:
        score += 10
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", resume_text):
        score += 10
    return min(score, 100)


def calculate_ats_score(keyword_data: dict, bullet_data: dict, experience_data: dict,
                        jd_text: str, resume_text: str) -> dict:
    req = required_years(jd_text)
    have = experience_data.get("total_years", 0.0)
    # No stated requirement -> experience doesn't penalise (fresher-friendly roles).
    exp_score = min(have / req, 1.0) * 100 if req > 0 else 100.0

    keyword_pct = keyword_data.get("match_percentage", 0.0)
    bullet_avg = bullet_data.get("average_score")
    # A resume with no detectable bullets gets a neutral bullet score rather than zero.
    bullet_pct = bullet_avg * 10 if bullet_avg is not None else 50.0
    format_score = format_quality_score(resume_text)

    breakdown = {
        "keyword_score": round(keyword_pct * W_KEYWORDS, 1),
        "bullet_score": round(bullet_pct * W_BULLETS, 1),
        "experience_score": round(exp_score * W_EXPERIENCE, 1),
        "format_score": round(format_score * W_FORMAT, 1),
    }
    ats = max(0, min(100, round(sum(breakdown.values()))))

    missing = len(keyword_data.get("missing_keywords", []))
    total = missing + len(keyword_data.get("matched_keywords", []))
    missing_pct = missing / total * 100 if total else 0
    if ats >= 80 and missing_pct <= 25:
        hire = "High"
    elif ats >= 60 or (ats >= 55 and missing_pct <= 30):
        hire = "Medium"
    else:
        hire = "Low"

    return {"ats_score": ats, "hire_probability": hire, "required_years": req, "score_breakdown": breakdown}


# ─────────────────────────────────────────────
# Stage 5: feedback
# ─────────────────────────────────────────────

FALLBACK_FEEDBACK = (
    "Add the missing keywords that genuinely match your experience, and rewrite weak bullets "
    "to show a measurable outcome (time saved, users served, errors reduced)."
)


async def feedback_stage(combined: dict) -> str:
    system = "You are a career counselor. Write honest, specific, actionable resume feedback. Plain text, no markdown."
    user = f"""Write 150-220 words of feedback for this resume against the job.

ATS score: {combined['ats_score']}/100
Keyword match: {combined['match_percentage']}% (missing: {', '.join(combined['missing_keywords'][:6]) or 'none'})
Bullet quality: {combined.get('average_score') or 'n/a'}/10
Experience: {combined['total_years']} years (role asks for {combined['required_years']})

Cover: overall assessment, 2 strengths, 2-3 gaps, 3 concrete next steps.
Do not tell the candidate to claim skills they don't have."""
    try:
        return await complete_text(system, user, temperature=0.4, max_tokens=450)
    except LLMError as e:
        logger.warning("Stage 5 failed, using fallback: %s", e)
        return FALLBACK_FEEDBACK


# ─────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────

def extract_job_title(jd_text: str) -> str:
    patterns = [
        r"(?:position|role|job title|title)\s*[:\-]\s*([^\n,|]{3,60})",
        r"(?:hiring|looking for|seeking)\s+(?:a|an)\s+([A-Za-z][A-Za-z /+#.-]{2,50}?)(?:\s+(?:to|who|with|at|for)\b|[.,\n])",
        r"^\s*([A-Za-z][A-Za-z /+#.-]{3,50})\s*$",
    ]
    for p in patterns:
        if m := re.search(p, jd_text, re.IGNORECASE | re.MULTILINE):
            return m.group(1).strip()[:60]
    return "Untitled role"


async def analyze_resume(resume_text: str, job_description: str) -> dict:
    resume_text = resume_text[:MAX_RESUME_CHARS]
    job_description = job_description[:MAX_JD_CHARS]

    keywords = await keyword_stage(resume_text, job_description)
    experience = calculate_experience(resume_text)
    bullets = await bullet_stage(resume_text, keywords["matched_keywords"] + keywords["missing_keywords"])
    score = calculate_ats_score(keywords, bullets, experience, job_description, resume_text)
    feedback = await feedback_stage({**keywords, **bullets, **experience, **score})

    weak = [b for b in bullets["bullet_analysis"] if b["score"] < 6]
    return {
        "ats_score": score["ats_score"],
        "hire_probability": score["hire_probability"],
        "score_breakdown": score["score_breakdown"],
        "matched_keywords": keywords["matched_keywords"],
        "missing_keywords": keywords["missing_keywords"],
        "match_percentage": keywords["match_percentage"],
        "bullet_analysis": bullets["bullet_analysis"],
        "weak_bullets": [b["original"] for b in weak],
        "improved_bullets": [b["improved"] for b in weak if b["improved"]],
        "experience_years": experience["total_years"],
        "experience_periods": experience["periods"],
        "required_years": score["required_years"],
        "overall_feedback": feedback,
        "job_title": extract_job_title(job_description),
    }


# Backwards-compatible name used by older imports.
call_grok = analyze_resume
