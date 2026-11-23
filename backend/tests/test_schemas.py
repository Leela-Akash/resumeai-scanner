import pytest
from pydantic import ValidationError

from services.schemas import BulletReview, KeywordSet


def test_keyword_set_cleans_garbage():
    ks = KeywordSet.model_validate({
        "technical_skills": ["Python", "python ", None, 3, "", "x" * 80],
        "tools_frameworks": ["Docker", "Python"],
        "certifications": "not a list",
    })
    assert ks.technical_skills == ["Python"]
    assert ks.hard_skills() == ["Python", "Docker"]


@pytest.mark.parametrize("raw,expected", [(7, 7), ("7/10", 7), (7.6, 8), (15, 10), (-2, 0)])
def test_bullet_score_is_normalised(raw, expected):
    assert BulletReview.model_validate({"score": raw}).score == expected


def test_bullet_score_must_be_numeric():
    with pytest.raises(ValidationError):
        BulletReview.model_validate({"score": "great"})
