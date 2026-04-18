import httpx
import json
import os

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


async def _groq_call(system: str, user: str, api_key: str) -> dict:
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        if response.status_code != 200:
            raise ValueError(f"Groq API error {response.status_code}: {response.text}")
    return _parse_json(response.json()["choices"][0]["message"]["content"])


async def extract_resume_data(resume_text: str, api_key: str) -> dict:
    system = (
        "You are an expert ATS system parser. Extract information with 100% accuracy. "
        "Return only valid JSON. No hallucination. If a field is not found, return empty list or null."
    )
    user = f"""Extract from this resume and return JSON only:

{{
  "full_name": "",
  "email": "",
  "phone": "",
  "total_experience": <number of years as float or null>,
  "current_title": "",
  "technical_skills": [],
  "soft_skills": [],
  "programming_languages": [],
  "frameworks": [],
  "cloud_platforms": [],
  "databases": [],
  "tools": [],
  "education": [{{"degree": "", "university": "", "year": ""}}],
  "certifications": []
}}

Resume:
{resume_text}"""
    return await _groq_call(system, user, api_key)


async def extract_jd_data(job_description: str, api_key: str) -> dict:
    system = (
        "You are an expert recruiter and ATS system. Parse job requirements precisely. "
        "Return only valid JSON. No hallucination. If a field is not found, return empty list or null."
    )
    user = f"""Extract from this job description and return JSON only:

{{
  "job_title": "",
  "required_skills": [],
  "preferred_skills": [],
  "required_years": <number or null>,
  "required_education": "",
  "key_responsibilities": [],
  "industry_keywords": [],
  "seniority_level": "<junior|mid|senior|lead|null>"
}}

Job Description:
{job_description}"""
    return await _groq_call(system, user, api_key)


async def generate_bullet_improvements(weak_bullets: list[dict], job_title: str, api_key: str) -> list[str]:
    if not weak_bullets:
        return []

    bullets_text = "\n".join(f"{i+1}. {b['bullet']}" for i, b in enumerate(weak_bullets))
    system = "You are an expert resume writer. Rewrite weak resume bullets to be strong, quantified, and ATS-optimized. Return only valid JSON."
    user = f"""Rewrite these weak resume bullets for a {job_title} role.
Each improved bullet must: start with an action verb, include metrics/numbers, be 10-25 words.

Weak bullets:
{bullets_text}

Return JSON only:
{{"improved": ["improved bullet 1", "improved bullet 2", ...]}}"""

    result = await _groq_call(system, user, api_key)
    return result.get("improved", [])


async def generate_overall_feedback(
    ats_score: int,
    resume_data: dict,
    jd_data: dict,
    breakdown: dict,
    api_key: str,
) -> tuple[str, str]:
    system = "You are a senior career coach. Give concise, actionable feedback. Return only valid JSON."
    user = f"""Given this ATS analysis, provide feedback:

ATS Score: {ats_score}/100
Job: {jd_data.get('job_title', '')} ({jd_data.get('seniority_level', '')})
Skills match: {breakdown.get('skills_match', 0)}/40
Experience match: {breakdown.get('experience_match', 0)}/25
Education match: {breakdown.get('education_match', 0)}/15
Keyword density: {breakdown.get('keyword_density', 0)}/20

Return JSON only:
{{
  "overall_feedback": "<2-3 sentence honest assessment>",
  "hire_probability": "<Low|Medium|High>"
}}"""
    result = await _groq_call(system, user, api_key)
    return result.get("overall_feedback", ""), result.get("hire_probability", "Medium")
