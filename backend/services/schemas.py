"""Pydantic models for everything the LLM returns. Invalid output never reaches scoring."""
from pydantic import BaseModel, Field, field_validator


def _clean_list(values: object, limit: int) -> list[str]:
    """Keep non-empty strings only, trimmed, de-duplicated case-insensitively, capped."""
    if not isinstance(values, list):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if not isinstance(v, str):
            continue
        s = " ".join(v.split()).strip(" .,;:-")
        if not s or len(s) > 60:
            continue
        key = s.lower()
        if key not in seen:
            seen.add(key)
            out.append(s)
        if len(out) >= limit:
            break
    return out


class KeywordSet(BaseModel):
    technical_skills: list[str] = Field(default_factory=list)
    tools_frameworks: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)

    @field_validator("*", mode="before")
    @classmethod
    def _clean(cls, v: object) -> list[str]:
        return _clean_list(v, limit=40)

    def hard_skills(self) -> list[str]:
        """Technical skills + tools + certifications, de-duplicated. These drive the score."""
        return _clean_list(self.technical_skills + self.tools_frameworks + self.certifications, limit=60)


class BulletReview(BaseModel):
    score: int = Field(ge=0, le=10)
    issues: list[str] = Field(default_factory=list)
    improved: str = ""

    @field_validator("score", mode="before")
    @classmethod
    def _coerce_score(cls, v: object) -> int:
        # Models sometimes return "7", 7.5 or "7/10". Normalise, then clamp to 0-10.
        if isinstance(v, str):
            v = v.split("/")[0].strip()
        try:
            n = round(float(v))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            raise ValueError(f"score is not a number: {v!r}")
        return max(0, min(10, n))

    @field_validator("issues", mode="before")
    @classmethod
    def _clean_issues(cls, v: object) -> list[str]:
        return [s for s in _clean_list(v, limit=4)]

    @field_validator("improved", mode="before")
    @classmethod
    def _clean_improved(cls, v: object) -> str:
        return " ".join(str(v or "").split())[:300]


class BulletBatch(BaseModel):
    reviews: list[BulletReview] = Field(default_factory=list)
