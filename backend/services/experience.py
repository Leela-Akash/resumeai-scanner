"""Work-experience calculation from resume text.

Only date ranges inside the Experience section count. Previously every range in the
resume counted, so a student's "B.Tech 2023 - 2027" showed up as ~3.9 years of experience.
"""
import re
from datetime import datetime

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
_PRESENT = {"present", "current", "now", "till date", "ongoing"}

_EXPERIENCE_HEADINGS = re.compile(
    r"^\s*(work experience|professional experience|experience|employment( history)?|"
    r"work history|internships?)\s*:?\s*$",
    re.IGNORECASE,
)
_OTHER_HEADINGS = re.compile(
    r"^\s*(education|academic.*|projects?|personal projects|skills|technical skills|"
    r"certifications?|achievements|awards|publications|summary|profile|objective|"
    r"leadership|activities|extra[- ]curricular.*|interests|languages)\s*:?\s*$",
    re.IGNORECASE,
)

_SEP = r"\s*(?:-|–|—|to)\s*"
_DATE = r"(?:[A-Za-z]{3,9}\.?\s+\d{4}|\d{1,2}[/-]\d{4}|\d{4})"
_RANGE = re.compile(rf"({_DATE}){_SEP}(present|current|now|ongoing|till date|{_DATE})", re.IGNORECASE)


def experience_section(text: str) -> str:
    """Return only the lines under an experience-type heading, or "" if there is none."""
    out: list[str] = []
    inside = False
    for line in text.splitlines():
        if _EXPERIENCE_HEADINGS.match(line):
            inside = True
            continue
        if _OTHER_HEADINGS.match(line):
            inside = False
            continue
        if inside:
            out.append(line)
    return "\n".join(out)


def _parse(s: str, now: datetime) -> datetime | None:
    s = s.strip().lower().rstrip(".")
    if s in _PRESENT:
        return now
    if m := re.fullmatch(r"(\d{1,2})[/-](\d{4})", s):
        month = int(m.group(1))
        return datetime(int(m.group(2)), month, 1) if 1 <= month <= 12 else None
    if m := re.fullmatch(r"([a-z]+)\.?\s+(\d{4})", s):
        month = _MONTHS.get(m.group(1)[:4] if m.group(1).startswith("sept") else m.group(1)[:3])
        return datetime(int(m.group(2)), month, 1) if month else None
    if m := re.fullmatch(r"(\d{4})", s):
        return datetime(int(m.group(1)), 1, 1)
    return None


def _months(start: datetime, end: datetime) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def calculate_experience(resume_text: str, now: datetime | None = None) -> dict:
    now = now or datetime.now()
    section = experience_section(resume_text)
    periods: list[tuple[datetime, datetime]] = []
    for m in _RANGE.finditer(section):
        start, end = _parse(m.group(1), now), _parse(m.group(2), now)
        if start and end and start <= end <= now and start.year >= 1980:
            periods.append((start, end))

    if not periods:
        return {"total_years": 0.0, "periods": []}

    periods.sort()
    merged = [periods[0]]
    for start, end in periods[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    total = sum(_months(s, e) for s, e in merged)
    period_list = []
    for s, e in merged:
        yrs, mos = divmod(_months(s, e), 12)
        label = f"{yrs} yr{'s' if yrs != 1 else ''}" if yrs else ""
        if mos or not yrs:
            label = (label + " " if label else "") + f"{mos} mo{'s' if mos != 1 else ''}"
        period_list.append({
            "start": s.strftime("%b %Y"),
            "end": "Present" if e == now else e.strftime("%b %Y"),
            "duration": label,
        })
    return {"total_years": round(total / 12, 1), "periods": period_list}


def required_years(jd_text: str) -> float:
    """'3+ years of experience', '2-4 yrs experience' -> lower bound."""
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:\+|\s*-\s*\d+)?\s*(?:years?|yrs?)\b(?:\s+of)?(?:\s+\w+){0,3}?\s+(?:experience|exp)\b",
        jd_text,
        re.IGNORECASE,
    )
    return float(m.group(1)) if m else 0.0
