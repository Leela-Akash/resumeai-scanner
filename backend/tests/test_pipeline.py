import pytest

from services import grok_service as pipeline
from services.llm import LLMError
from services.schemas import BulletBatch, KeywordSet

RESUME = """Akash
akash@example.com
Experience
Intern, Acme
Jun 2025 - Aug 2025
• Built REST APIs in Spring Boot for 3 internal tools
• Worked on frontend pages for the dashboard
Education
B.Tech 2023 - 2027
Skills
Java, Spring Boot, React, Docker
Projects
• Developed a banking app with JWT auth and PostgreSQL
"""
JD = "We are looking for a Backend Engineer. Skills: Java, Spring Boot, Kafka, Docker. Freshers welcome."


def install_fakes(monkeypatch, reviews=None):
    async def fake_json(system, user, model, **_):
        if model is KeywordSet:
            if "JOB DESCRIPTION" in user:
                return KeywordSet(technical_skills=["Java", "Kafka"], tools_frameworks=["Spring Boot", "Docker"])
            return KeywordSet(technical_skills=["Java"], tools_frameworks=["Spring Boot", "React", "Docker"])
        if model is BulletBatch:
            return BulletBatch.model_validate({"reviews": reviews if reviews is not None else [
                {"score": 8, "issues": []},
                {"score": 3, "issues": ["No outcome"], "improved": "Built [N] dashboard pages in React"},
                {"score": 6, "issues": []},
            ]})
        raise AssertionError(model)

    async def fake_text(*_, **__):
        return "Solid backend fundamentals."

    monkeypatch.setattr(pipeline, "complete_json", fake_json)
    monkeypatch.setattr(pipeline, "complete_text", fake_text)


@pytest.mark.asyncio
async def test_full_pipeline(monkeypatch):
    install_fakes(monkeypatch)
    r = await pipeline.analyze_resume(RESUME, JD)

    assert r["matched_keywords"] == ["Java", "Spring Boot", "Docker"]
    assert r["missing_keywords"] == ["Kafka"]
    assert r["experience_years"] == 0.2  # internship only, not the B.Tech years
    assert r["weak_bullets"] == ["Worked on frontend pages for the dashboard"]
    assert r["improved_bullets"] == ["Built [N] dashboard pages in React"]
    assert r["job_title"] == "Backend Engineer"
    b = r["score_breakdown"]
    assert b["keyword_score"] == 30.0          # 75% * 0.40
    assert b["bullet_score"] == 17.1           # avg 5.7/10 -> 57 * 0.30
    assert b["experience_score"] == 20.0       # no requirement stated
    assert b["format_score"] > 0               # was always 0 before the fix
    assert r["ats_score"] == round(sum(b.values()))


@pytest.mark.asyncio
async def test_bullet_count_mismatch_is_an_error(monkeypatch):
    install_fakes(monkeypatch, reviews=[{"score": 5}])
    with pytest.raises(LLMError):
        await pipeline.analyze_resume(RESUME, JD)


def test_format_score_uses_resume_text():
    assert pipeline.format_quality_score(RESUME) >= 70
    assert pipeline.format_quality_score("") == 0


def test_extract_bullets_dedupes():
    text = "• Built a thing that is long enough\n• Built a thing that is long enough\nshort"
    assert pipeline.extract_bullets(text) == ["Built a thing that is long enough"]
