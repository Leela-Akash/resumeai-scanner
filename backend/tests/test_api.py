import fitz
import pytest
from fastapi.testclient import TestClient

import main
from routes import analyze as analyze_route
from services.llm import LLMError

JD = "We are hiring a Backend Engineer with Java, Spring Boot and Docker. Freshers welcome to apply."
AUTH = {"Authorization": "Bearer user1"}


def make_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(50, 50, 550, 800), text)
    data = doc.tobytes()
    doc.close()
    return data


RESUME_PDF = make_pdf("Experience\n" + "Built REST APIs with Spring Boot and Docker for internal tools. " * 6)


@pytest.fixture
def client(store, monkeypatch):
    main.limiter.reset()

    async def fake_analyze(text, jd):
        return {"ats_score": 72, "job_title": "Backend Engineer", "matched_keywords": ["Java"]}

    monkeypatch.setattr(analyze_route, "analyze_resume", fake_analyze)
    return TestClient(main.app)


def post(client, pdf=RESUME_PDF, jd=JD, headers=AUTH):
    return client.post(
        "/api/analyze",
        files={"resume": ("r.pdf", pdf, "application/pdf")},
        data={"job_description": jd},
        headers=headers,
    )


def test_health(client):
    assert client.get("/health").json()["status"] == "healthy"


def test_requires_auth(client):
    assert post(client, headers={}).status_code in (401, 403)
    assert post(client, headers={"Authorization": "Bearer nope"}).status_code == 401


def test_success_saves_scan_and_counts(client, store):
    r = post(client)
    assert r.status_code == 200
    assert r.json()["ats_score"] == 72
    assert r.json()["id"] == "scan1"
    assert store.users["user1"]["scansUsed"] == 1


def test_rejects_non_pdf_even_with_pdf_content_type(client):
    r = post(client, pdf=b"MZ\x90\x00 definitely not a pdf")
    assert r.status_code == 400


def test_rejects_short_job_description(client):
    assert post(client, jd="Java dev").status_code == 400


def test_rejects_image_only_pdf(client):
    blank = fitz.open(); blank.new_page(); data = blank.tobytes(); blank.close()
    r = post(client, pdf=data)
    assert r.status_code == 422
    assert "scanned image" in r.json()["detail"]


def test_ai_failure_returns_friendly_503(client, monkeypatch):
    async def boom(*_):
        raise LLMError("Groq HTTP 500: internal details")

    monkeypatch.setattr(analyze_route, "analyze_resume", boom)
    r = post(client)
    assert r.status_code == 503
    assert "internal details" not in r.json()["detail"]


def test_free_limit_enforced_when_configured(client, store, monkeypatch):
    monkeypatch.setenv("FREE_SCAN_LIMIT", "1")
    assert post(client).status_code == 200
    r = post(client)
    assert r.status_code == 403
    assert r.json()["detail"] == "FREE_LIMIT_REACHED"


def test_no_limit_by_default(client, store, monkeypatch):
    monkeypatch.delenv("FREE_SCAN_LIMIT", raising=False)
    for _ in range(4):
        assert post(client).status_code == 200


def test_history(client, store):
    post(client)
    r = client.get("/api/history", headers=AUTH)
    assert r.status_code == 200 and len(r.json()) == 1
