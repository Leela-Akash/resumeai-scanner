import httpx
import pytest

from services import llm
from services.llm import LLMError, complete_json, parse_json_object
from services.schemas import KeywordSet


def test_parse_json_object_handles_fences_and_prose():
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_object('Here you go: {"a": 1} hope it helps') == {"a": 1}


def _mock_client(monkeypatch, responses):
    calls = iter(responses)

    def handler(request):
        status, body = next(calls)
        return httpx.Response(status, json=body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(llm, "_get_client", lambda: client)

    async def no_sleep(_):
        return None

    monkeypatch.setattr(llm.asyncio, "sleep", no_sleep)


def _ok(content):
    return 200, {"choices": [{"message": {"content": content}}]}


@pytest.mark.asyncio
async def test_retries_on_server_error(monkeypatch):
    _mock_client(monkeypatch, [(503, {}), (429, {}), _ok('{"technical_skills": ["Go"]}')])
    result = await complete_json("s", "u", KeywordSet)
    assert result.technical_skills == ["Go"]


@pytest.mark.asyncio
async def test_does_not_retry_auth_errors(monkeypatch):
    _mock_client(monkeypatch, [(401, {"error": "bad key"})])
    with pytest.raises(LLMError, match="HTTP 401"):
        await complete_json("s", "u", KeywordSet)


@pytest.mark.asyncio
async def test_retries_once_on_invalid_json(monkeypatch):
    _mock_client(monkeypatch, [_ok("not json"), _ok('{"soft_skills": ["Communication"]}')])
    result = await complete_json("s", "u", KeywordSet)
    assert result.soft_skills == ["Communication"]


@pytest.mark.asyncio
async def test_gives_up_after_max_retries(monkeypatch):
    _mock_client(monkeypatch, [(500, {})] * 3)
    with pytest.raises(LLMError, match="unavailable"):
        await complete_json("s", "u", KeywordSet)
