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
    """What the LLM judges about one bullet. The score itself is computed in code."""
    shows_outcome: bool = False
    improved: str = ""

    @field_validator("shows_outcome", mode="before")
    @classmethod
    def _coerce_bool(cls, v: object) -> bool:
        if isinstance(v, str):
            return v.strip().lower() in {"true", "yes", "1"}
        return bool(v)

    @field_validator("improved", mode="before")
    @classmethod
    def _clean_improved(cls, v: object) -> str:
        return " ".join(str(v or "").split())[:300]


class BulletBatch(BaseModel):
    reviews: list[BulletReview] = Field(default_factory=list)
