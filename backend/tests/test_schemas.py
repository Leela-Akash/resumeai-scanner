import pytest

from services.schemas import BulletReview, KeywordSet


def test_keyword_set_cleans_garbage():
    ks = KeywordSet.model_validate({
        "technical_skills": ["Python", "python ", None, 3, "", "x" * 80],
        "tools_frameworks": ["Docker", "Python"],
        "certifications": "not a list",
    })
    assert ks.technical_skills == ["Python"]
    assert ks.hard_skills() == ["Python", "Docker"]


@pytest.mark.parametrize("raw,expected", [(True, True), ("true", True), ("no", False), (None, False)])
def test_shows_outcome_is_coerced(raw, expected):
    assert BulletReview.model_validate({"shows_outcome": raw}).shows_outcome is expected
