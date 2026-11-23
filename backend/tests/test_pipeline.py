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
                {"shows_outcome": True, "improved": ""},
                {"shows_outcome": False, "improved": "Built [N] dashboard pages in React, used by 500 staff"},
                {"shows_outcome": False, "improved": ""},
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
    assert r["weak_bullets"] == [
        "Worked on frontend pages for the dashboard",
        "Developed a banking app with JWT auth and PostgreSQL",
    ]
    # The invented "500" is replaced with a placeholder.
    assert r["improved_bullets"] == ["Built [N] dashboard pages in React, used by [X] staff"]
    assert r["job_title"] == "Backend Engineer"
    b = r["score_breakdown"]
    assert b["keyword_score"] == 30.0          # 75% * 0.40
    # Rubric (metric 3, verb 2, outcome 3, skills 2): 3+2+3+2=10, 0+0+0+0=0, 0+2+0+0=2 -> avg 4.0
    assert [x["score"] for x in r["bullet_analysis"]] == [10, 0, 2]
    assert b["bullet_score"] == 12.0
    assert b["experience_score"] == 20.0       # no requirement stated
    assert b["format_score"] > 0               # was always 0 before the fix
    assert r["ats_score"] == round(sum(b.values()))


@pytest.mark.asyncio
async def test_bullet_count_mismatch_is_an_error(monkeypatch):
    install_fakes(monkeypatch, reviews=[{"shows_outcome": True}])
    with pytest.raises(LLMError):
        await pipeline.analyze_resume(RESUME, JD)


def test_format_score_uses_resume_text():
    assert pipeline.format_quality_score(RESUME) >= 70
    assert pipeline.format_quality_score("") == 0


def test_extract_bullets_dedupes():
    text = "• Built a thing that is long enough\n• Built a thing that is long enough\nEducation"
    assert pipeline.extract_bullets(text) == ["Built a thing that is long enough"]


def test_wrapped_bullets_without_glyphs_are_rejoined():
    # What PyMuPDF returns for an HTML/Chrome PDF: no bullet glyphs, long lines wrapped.
    text = """PROJECTS
Online Banking System | React, Spring Boot
Jul – Nov 2025
Built a React (Vite) frontend for customer, staff and admin roles, consuming JWT-secured REST APIs via Axios for
accounts, fund transfers, loans and notifications.
Designed the Spring Boot backend with safe fund transfers and role-
based access control.
EDUCATION
KL University"""
    assert pipeline.extract_bullets(text) == [
        "Built a React (Vite) frontend for customer, staff and admin roles, consuming JWT-secured REST APIs via Axios for accounts, fund transfers, loans and notifications.",
        "Designed the Spring Boot backend with safe fund transfers and role-based access control.",
    ]


def test_bullet_score_is_deterministic():
    jd = ["SQL", "API design", "Docker"]
    score, issues = pipeline.score_bullet("Designed REST APIs in Spring Boot used by 3 teams", False, jd)
    assert score == 7  # metric + verb + skills (REST proves API design)
    assert issues == ["Say what changed because of your work"]
    assert pipeline.score_bullet("Worked on frontend pages", False, jd)[0] == 0


def test_years_are_not_metrics():
    assert not pipeline.has_metric("Built a dashboard in 2024")
    assert pipeline.has_metric("Led a team of 4")


def test_sanitize_rewrite_keeps_only_original_numbers():
    out = pipeline.sanitize_rewrite("Served 100+ teams", "Served 100+ teams with 99.9% uptime for [N users]")
    assert out == "Served 100+ teams with [X%] uptime for [N users]"
