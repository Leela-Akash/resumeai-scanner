import httpx
import json
import os

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "You are an expert ATS resume analyzer and career coach with 10 years experience. "
    "Always respond with valid JSON only, no extra text."
)

USER_PROMPT_TEMPLATE = """Analyze this resume against the job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return this exact JSON structure:
{{
  "ats_score": <number 0-100>,
  "matched_keywords": [<list of strings>],
  "missing_keywords": [<list of strings>],
  "weak_bullets": [<list of weak bullet strings>],
  "improved_bullets": [<list of improved versions>],
  "overall_feedback": "<string>",
  "hire_probability": "<Low or Medium or High>",
  "job_title": "<extracted job title from JD>"
}}"""


async def call_grok(resume_text: str, job_description: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set")

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    resume_text=resume_text,
                    job_description=job_description,
                ),
            },
        ],
        "temperature": 0.3,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if response.status_code != 200:
            raise ValueError(f"Grok API error {response.status_code}: {response.text}")

    raw = response.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown code fences if Grok wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)
