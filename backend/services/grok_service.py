import asyncio
import json
import logging
import os
import re
from datetime import datetime

import httpx
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0.3
MAX_TOKENS = 2000
MAX_RETRIES = 3


# ─────────────────────────────────────────────
# Core helpers
# ─────────────────────────────────────────────

def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try extracting JSON object from response
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        return {"score": 5, "issues": ["Unable to analyze"]}


async def _groq_call(system: str, user: str, api_key: str) -> dict:
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(GROQ_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                return _parse_json(response.json()["choices"][0]["message"]["content"])
            if response.status_code == 429:
                await asyncio.sleep(2 ** attempt)
                continue
            raise ValueError(f"Groq error {response.status_code}: {response.text}")
        except (json.JSONDecodeError, KeyError) as e:
            if attempt == MAX_RETRIES - 1:
                raise ValueError(f"Failed to parse Groq response: {e}")
            await asyncio.sleep(1)
    raise ValueError("Groq API failed after max retries")


def _fuzzy_match(kw1: str, kw2: str) -> bool:
    return fuzz.partial_ratio(kw1.lower(), kw2.lower()) >= 85


# ─────────────────────────────────────────────
# Stage 1: Keyword extraction & fuzzy matching
# ─────────────────────────────────────────────

async def extract_and_match_keywords(resume_text: str, jd_text: str, api_key: str) -> dict:
    logger.info("Stage 1: Keyword extraction started")
    system = "You are an ATS keyword extraction expert. Return only valid JSON, no extra text."

    jd_prompt = f"""Extract all keywords from this job description.

JD:
{jd_text}

Return JSON only:
{{
  "technical_skills": [],
  "soft_skills": [],
  "tools_frameworks": [],
  "certifications": []
}}"""

    resume_prompt = f"""Extract all keywords from this resume.

Resume:
{resume_text}

Return JSON only:
{{
  "technical_skills": [],
  "soft_skills": [],
  "tools_frameworks": [],
  "certifications": []
}}"""

    jd_data, resume_data = await asyncio.gather(
        _groq_call(system, jd_prompt, api_key),
        _groq_call(system, resume_prompt, api_key),
    )

    def flatten(d: dict) -> list:
        return (
            d.get("technical_skills", []) +
            d.get("soft_skills", []) +
            d.get("tools_frameworks", []) +
            d.get("certifications", [])
        )

    jd_keywords = flatten(jd_data)
    resume_keywords = flatten(resume_data)

    matched, missing = [], []
    for jd_kw in jd_keywords:
        if any(_fuzzy_match(jd_kw, r_kw) for r_kw in resume_keywords):
            matched.append(jd_kw)
        else:
            missing.append(jd_kw)

    match_pct = round((len(matched) / len(jd_keywords) * 100), 1) if jd_keywords else 0.0

    logger.info(f"Stage 1 done: {len(matched)} matched, {len(missing)} missing")
    return {
        "matched_keywords": matched,
        "missing_keywords": missing,
        "match_percentage": match_pct,
    }


# ─────────────────────────────────────────────
# Stage 2: Bullet point analysis
# ─────────────────────────────────────────────

TECH_PATTERNS = re.compile(
    r'\b(Python|Java|JavaScript|TypeScript|React|Angular|Vue|Node\.?js|FastAPI|Django|Flask|'
    r'Spring|Express|Docker|Kubernetes|AWS|GCP|Azure|PostgreSQL|MySQL|MongoDB|Redis|'
    r'GraphQL|REST|Kafka|Terraform|CI/CD|Jenkins|Git|Linux|Nginx|Spark|TensorFlow|'
    r'PyTorch|Pandas|NumPy|Scikit|Hadoop|Airflow|Elasticsearch|Firebase|Supabase|'
    r'Next\.?js|Tailwind|HTML|CSS|SQL|NoSQL|Microservices|Serverless)\b',
    re.IGNORECASE
)

BACKEND_WORDS  = {"api", "backend", "microservice", "fastapi", "django", "flask", "spring", "server", "endpoint", "rest", "graphql"}
FRONTEND_WORDS = {"frontend", "react", "angular", "vue", "ui", "ux", "dashboard", "interface", "component", "html", "css", "next"}
DEVOPS_WORDS   = {"docker", "kubernetes", "deploy", "ci/cd", "jenkins", "pipeline", "terraform", "infrastructure", "cloud", "aws", "gcp", "azure"}
DB_WORDS       = {"database", "sql", "mysql", "postgres", "mongodb", "redis", "schema", "query", "firebase", "nosql", "orm"}

TEMPLATES = {
    "backend": [
        "Architected {tech} backend handling {scale} using {extra}",
        "Built {tech} REST API serving {scale} with sub-100ms response time",
        "Developed {tech} microservice processing {volume} daily requests using {extra}",
        "Engineered {tech} service handling {scale} with 99.9% uptime",
    ],
    "frontend": [
        "Designed {tech} interface for {scale} with real-time updates",
        "Built responsive {tech} dashboard serving {scale}",
        "Implemented {tech} components with sub-2s load time and smooth UX",
        "Developed {tech} UI handling {scale} with optimized rendering",
    ],
    "devops": [
        "Containerized {number} services with {tech}, reducing deployment time from 2 hours to 15 minutes",
        "Automated {tech} pipeline using {extra}, cutting release cycle by 60%",
        "Deployed {tech} infrastructure on {extra} supporting {scale}",
        "Streamlined CI/CD pipeline with {tech}, enabling {number} deployments per day",
    ],
    "database": [
        "Designed {tech} schema supporting {volume} records with sub-100ms query time",
        "Optimized {tech} queries reducing latency from 500ms to 50ms",
        "Architected {tech} database handling {scale} with 99.9% uptime",
        "Migrated legacy data to {tech}, improving query performance by 70%",
    ],
    "fullstack": [
        "Built end-to-end {tech} application serving {scale} using {extra}",
        "Developed full-stack {tech} platform for {scale} with {extra} backend",
        "Architected {tech} solution handling {scale} across frontend and backend",
        "Delivered {tech} product serving {scale} with {extra} integration",
    ],
}

SCALE_OPTIONS  = ["5K daily users", "1K concurrent users", "10K monthly active users", "50 concurrent users", "100K requests/month"]
VOLUME_OPTIONS = ["10K", "50K", "100K", "1M"]
NUMBER_OPTIONS = ["5", "8", "12", "3"]


def _extract_technologies(bullet: str) -> list[str]:
    return list(dict.fromkeys(TECH_PATTERNS.findall(bullet)))


def _categorize_bullet(bullet: str, tech: list) -> str:
    words = set(bullet.lower().split())
    tech_lower = {t.lower() for t in tech}
    if words & DEVOPS_WORDS or tech_lower & {"docker", "kubernetes", "terraform", "aws", "gcp", "azure"}:
        return "devops"
    if words & DB_WORDS:
        return "database"
    if words & FRONTEND_WORDS or tech_lower & {"react", "angular", "vue", "html", "css"}:
        return "frontend"
    if words & BACKEND_WORDS:
        return "backend"
    return "fullstack"


def _improve_bullet(bullet: str, jd_keywords: list) -> str:
    import random
    tech = _extract_technologies(bullet)
    category = _categorize_bullet(bullet, tech)

    # Build tech string — use real tech from bullet + 1 missing JD keyword
    missing_tech = [k for k in jd_keywords if k not in bullet][:1]
    primary = tech[0] if tech else (jd_keywords[0] if jd_keywords else "Python")
    secondary = tech[1] if len(tech) > 1 else (missing_tech[0] if missing_tech else jd_keywords[0] if jd_keywords else "REST APIs")
    tech_str = f"{primary}/{secondary}" if secondary and secondary != primary else primary

    # Preserve existing metric if present
    existing_metric = re.search(r'\d+[%xX]?\s*(?:ms|s|hours?|minutes?|days?|users?|requests?|records?|services?)?', bullet)
    scale = existing_metric.group().strip() if existing_metric else random.choice(SCALE_OPTIONS)
    volume = existing_metric.group().strip() if existing_metric else random.choice(VOLUME_OPTIONS)
    number = re.search(r'\b(\d+)\b', bullet)
    number = number.group(1) if number else random.choice(NUMBER_OPTIONS)

    template = random.choice(TEMPLATES[category])
    improved = template.format(
        tech=primary,
        extra=secondary,
        scale=scale,
        volume=volume,
        number=number,
    )
    return improved


def _extract_bullets(resume_text: str) -> list[str]:
    bullets = []
    for line in resume_text.splitlines():
        line = line.strip()
        if not line or len(line) < 20:
            continue
        if re.match(r'^[•·\-–*►▪▸○]', line):
            cleaned = re.sub(r'^[•·\-–*►▪▸○]+\s*', '', line).strip()
            if cleaned:
                bullets.append(cleaned)
        elif re.match(
            r'^(Led|Built|Designed|Developed|Implemented|Architected|Optimized|'
            r'Deployed|Automated|Managed|Created|Launched|Improved|Reduced|'
            r'Increased|Delivered|Streamlined|Engineered|Migrated|Integrated)',
            line
        ):
            bullets.append(line)
    return bullets[:15]


async def _score_bullet(bullet: str, jd_keywords: list, api_key: str) -> dict:
    system = "You are a resume expert. Score bullets with partial credit. Return only valid JSON, no markdown."
    user = f"""Score this resume bullet point on a scale of 0-10. Award partial credit:

Scoring rubric:
- Contains a number/metric/percentage? → +3 points
  Example: "Reduced latency by 40%", "Led team of 5", "Processed 10K records"

- Starts with strong action verb? → +2 points
  Strong verbs: Architected, Implemented, Designed, Optimized, Led, Built, Deployed
  Weak verbs: Worked on, Responsible for, Helped with, Assisted, Involved in

- Shows measurable impact/outcome? → +3 points
  Good: "Improved performance by 50%" (clear outcome)
  Bad: "Implemented caching layer" (no outcome shown)

- Matches job description keywords? → +2 points
  JD keywords: {', '.join(jd_keywords[:20])}

Be GENEROUS with partial credit. A bullet with just a metric and weak verb should score 4-5, not 0-1.

Bullet to score: {bullet}

Return ONLY valid JSON (no markdown):
{{"score": 5, "issues": ["Use stronger action verb", "Add impact metric"]}}"""

    try:
        return await _groq_call(system, user, api_key)
    except Exception:
        return {"score": 5, "issues": ["Unable to analyze"]}


async def analyze_bullet_points(resume_text: str, jd_text: str, jd_keywords: list, api_key: str) -> dict:
    logger.info("Stage 2: Bullet analysis started")
    bullets = _extract_bullets(resume_text)

    if not bullets:
        return {"bullet_analysis": [], "average_score": 5.0, "weak_bullets_count": 0}

    # Score all bullets in parallel via Groq
    score_tasks = [_score_bullet(b, jd_keywords, api_key) for b in bullets[:8]]
    scores = await asyncio.gather(*score_tasks, return_exceptions=True)

    bullet_analysis = []
    for bullet, score_data in zip(bullets[:8], scores):
        if isinstance(score_data, Exception):
            score_data = {"score": 5, "issues": []}
        score = score_data.get("score", 5)
        improved = _improve_bullet(bullet, jd_keywords) if score < 6 else ""
        bullet_analysis.append({
            "original": bullet,
            "score": score,
            "issues": score_data.get("issues", []),
            "improved": improved,
        })

    avg = round(sum(b["score"] for b in bullet_analysis) / len(bullet_analysis), 1)
    weak_count = sum(1 for b in bullet_analysis if b["score"] < 6)

    logger.info(f"Stage 2 done: avg score {avg}, {weak_count} weak bullets")
    return {
        "bullet_analysis": bullet_analysis,
        "average_score": avg,
        "weak_bullets_count": weak_count,
    }


# ─────────────────────────────────────────────
# Stage 3: Experience calculation
# ─────────────────────────────────────────────

def calculate_experience(resume_text: str) -> dict:
    logger.info("Stage 3: Experience calculation started")
    now = datetime.now()

    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10,
        "november": 11, "december": 12,
    }

    def parse_date(s: str):
        s = s.strip().lower()
        if s in ("present", "current", "now", "till date"):
            return now
        # MM/YYYY or MM-YYYY
        m = re.match(r'(\d{1,2})[/\-](\d{4})', s)
        if m:
            return datetime(int(m.group(2)), int(m.group(1)), 1)
        # Month YYYY
        m = re.match(r'([a-z]+)\s+(\d{4})', s)
        if m and m.group(1) in month_map:
            return datetime(int(m.group(2)), month_map[m.group(1)], 1)
        # YYYY only
        m = re.match(r'(\d{4})', s)
        if m:
            return datetime(int(m.group(1)), 1, 1)
        return None

    patterns = [
        r'([A-Za-z]+\.?\s+\d{4})\s*[-–to]+\s*(present|current|[A-Za-z]+\.?\s+\d{4})',
        r'(\d{1,2}[/\-]\d{4})\s*[-–to]+\s*(present|current|\d{1,2}[/\-]\d{4})',
        r'(\d{4})\s*[-–to]+\s*(present|current|\d{4})',
    ]

    periods = []
    for pattern in patterns:
        for match in re.finditer(pattern, resume_text, re.IGNORECASE):
            start = parse_date(match.group(1))
            end = parse_date(match.group(2))
            if start and end and end >= start:
                periods.append((start, end))

    if not periods:
        logger.info("Stage 3 done: no date ranges found")
        return {"total_years": 0.0, "periods": []}

    # Merge overlapping periods
    periods.sort(key=lambda x: x[0])
    merged = [periods[0]]
    for start, end in periods[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    total_months = sum((e.year - s.year) * 12 + (e.month - s.month) for s, e in merged)
    total_years = round(total_months / 12, 1)

    period_list = []
    for s, e in merged:
        months = (e.year - s.year) * 12 + (e.month - s.month)
        yrs, mos = divmod(months, 12)
        label = f"{yrs} yr{'s' if yrs != 1 else ''}" + (f" {mos} mo{'s' if mos != 1 else ''}" if mos else "")
        period_list.append({"start": s.strftime("%b %Y"), "end": e.strftime("%b %Y") if e != now else "Present", "duration": label})

    logger.info(f"Stage 3 done: {total_years} total years")
    return {"total_years": total_years, "periods": period_list}


# ─────────────────────────────────────────────
# Stage 4: ATS score calculation
# ─────────────────────────────────────────────

def _format_quality_score(resume_text: str) -> int:
    score = 0
    text_lower = resume_text.lower()
    if any(s in text_lower for s in ["experience", "work history", "employment"]):
        score += 30
    if any(s in text_lower for s in ["skills", "technical skills", "competencies"]):
        score += 15
    if any(s in text_lower for s in ["education", "degree", "university", "college"]):
        score += 15
    bullet_count = len(re.findall(r'^[•·\-–*►▪▸]', resume_text, re.MULTILINE))
    if bullet_count >= 5:
        score += 20
    date_count = len(re.findall(r'\d{4}', resume_text))
    if date_count >= 2:
        score += 20
    return min(score, 100)


async def calculate_ats_score(
    keyword_data: dict,
    bullet_data: dict,
    experience_data: dict,
    jd_text: str,
    api_key: str,
) -> dict:
    logger.info("Stage 4: ATS score calculation started")

    # Extract required years from JD
    required_years = 0.0
    m = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)', jd_text, re.IGNORECASE)
    if m:
        required_years = float(m.group(1))

    resume_years = experience_data.get("total_years", 0.0)
    exp_score = min(resume_years / required_years, 1.0) * 100 if required_years > 0 else 70.0

    keyword_pct = keyword_data.get("match_percentage", 0.0)
    bullet_avg = bullet_data.get("average_score", 5.0)
    format_score = _format_quality_score("")

    ats_score = round(
        (keyword_pct * 0.40) +
        (bullet_avg * 10 * 0.30) +
        (exp_score * 0.20) +
        (format_score * 0.10)
    )
    ats_score = max(0, min(100, ats_score))

    missing_count = len(keyword_data.get("missing_keywords", []))
    total_count = len(keyword_data.get("matched_keywords", [])) + missing_count
    missing_pct = (missing_count / total_count * 100) if total_count > 0 else 0

    if ats_score >= 80 and missing_pct <= 25:
        hire_probability = "High"
    elif ats_score >= 60 or (ats_score >= 55 and missing_pct <= 30):
        hire_probability = "Medium"
    else:
        hire_probability = "Low"

    logger.info(f"Stage 4 done: ATS={ats_score}, hire={hire_probability}")
    return {
        "ats_score": ats_score,
        "hire_probability": hire_probability,
        "required_years": required_years,
        "score_breakdown": {
            "keyword_score": round(keyword_pct * 0.40, 1),
            "bullet_score": round((bullet_avg / 10) * 100 * 0.30, 1),
            "experience_score": round(exp_score * 0.20, 1),
            "format_score": round(format_score * 0.10, 1),
        },
    }


# ─────────────────────────────────────────────
# Stage 5: Overall feedback generation
# ─────────────────────────────────────────────

async def generate_feedback(combined: dict, api_key: str) -> str:
    logger.info("Stage 5: Feedback generation started")
    system = "You are a professional career counselor. Write honest, actionable resume feedback."
    top_missing = combined.get("missing_keywords", [])[:5]

    user = f"""Generate professional resume feedback (200-300 words):

ATS Score: {combined.get('ats_score')}/100
Keyword match: {combined.get('match_percentage')}% ({len(combined.get('missing_keywords', []))} missing)
Bullet quality: {combined.get('average_score')}/10
Experience: {combined.get('total_years')} years vs {combined.get('required_years', 0)} required
Top missing keywords: {', '.join(top_missing)}

Structure:
1. Overall assessment (1-2 sentences)
2. 2-3 strengths
3. 2-3 critical gaps
4. 3 specific action items
5. Encouraging closing line

Tone: Professional but supportive, like a career counselor."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GROQ_API_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.5,
                    "max_tokens": 400,
                },
            )
        if response.status_code == 200:
            feedback = response.json()["choices"][0]["message"]["content"].strip()
            logger.info("Stage 5 done")
            return feedback
    except Exception as e:
        logger.error(f"Stage 5 failed: {e}")

    return "Your resume shows relevant experience. Focus on adding quantifiable metrics to your bullet points and including the missing keywords to improve your ATS score."


# ─────────────────────────────────────────────
# Main orchestrator
# ─────────────────────────────────────────────

def _extract_job_title(jd_text: str) -> str:
    patterns = [
        r'(?:position|role|title|job title)[:\s]+([A-Za-z\s/]+)',
        r'^([A-Za-z\s/]{3,50})\n',
        r'(?:hiring|looking for|seeking)\s+(?:a|an)\s+([A-Za-z\s/]+)',
    ]
    for pattern in patterns:
        m = re.search(pattern, jd_text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()[:60]
    return "Software Engineer"


async def call_grok(resume_text: str, job_description: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set")

    # Stage 1 & 3 in parallel (Stage 3 is sync so wrap it)
    keyword_results, experience_results = await asyncio.gather(
        extract_and_match_keywords(resume_text, job_description, api_key),
        asyncio.to_thread(calculate_experience, resume_text),
    )

    # Stage 2 needs keywords from Stage 1
    bullet_results = await analyze_bullet_points(
        resume_text,
        job_description,
        keyword_results["matched_keywords"] + keyword_results["missing_keywords"],
        api_key,
    )

    # Stage 4
    score_results = await calculate_ats_score(
        keyword_results,
        bullet_results,
        experience_results,
        job_description,
        api_key,
    )

    # Stage 5
    feedback = await generate_feedback(
        {
            **keyword_results,
            **bullet_results,
            **experience_results,
            **score_results,
        },
        api_key,
    )

    weak = [b for b in bullet_results["bullet_analysis"] if b["score"] < 6]

    return {
        "ats_score": score_results["ats_score"],
        "matched_keywords": keyword_results["matched_keywords"],
        "missing_keywords": keyword_results["missing_keywords"],
        "weak_bullets": [b["original"] for b in weak],
        "improved_bullets": [b["improved"] for b in weak if b.get("improved")],
        "overall_feedback": feedback,
        "hire_probability": score_results["hire_probability"],
        "job_title": _extract_job_title(job_description),
        "experience_years": experience_results.get("total_years", 0),
        "score_breakdown": score_results["score_breakdown"],
        "bullet_analysis": bullet_results["bullet_analysis"],
    }
