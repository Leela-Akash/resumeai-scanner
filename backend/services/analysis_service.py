import re
from difflib import SequenceMatcher
from data.keywords import ATS_POWER_WORDS, WEAK_WORDS, EDUCATION_LEVELS


# ── Fuzzy match ────────────────────────────────────────────────────────────────

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_fuzzy_match(skill: str, resume_skills: list[str], threshold: float = 0.8) -> bool:
    for rs in resume_skills:
        if _similarity(skill, rs) >= threshold:
            return True
        # handle "React" vs "React.js" / "Node" vs "Node.js"
        if skill.lower().rstrip(".js") == rs.lower().rstrip(".js"):
            return True
        if skill.lower() in rs.lower() or rs.lower() in skill.lower():
            return True
    return False


# ── Education matching ─────────────────────────────────────────────────────────

def match_education(required_edu: str, resume_edu: list[dict]) -> int:
    if not required_edu:
        return 15  # no requirement = full score

    req_level = 0
    for key, val in EDUCATION_LEVELS.items():
        if key in required_edu.lower():
            req_level = val
            break

    resume_level = 0
    for edu in resume_edu:
        degree = edu.get("degree", "").lower()
        for key, val in EDUCATION_LEVELS.items():
            if key in degree:
                resume_level = max(resume_level, val)

    if resume_level >= req_level:
        return 15
    elif resume_level == req_level - 1:
        return 10
    return 5


# ── Experience calculator ──────────────────────────────────────────────────────

def calculate_experience_years(resume_text: str) -> float:
    current_year = 2026
    patterns = [
        r'(\d{4})\s*[-–]\s*(present|\d{4})',
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]+(\d{4})\s*[-–]\s*(present|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]+(\d{4}))',
    ]

    year_ranges = re.findall(patterns[0], resume_text.lower())
    total_months = 0
    seen = set()

    for start, end in year_ranges:
        try:
            start_year = int(start)
            end_year = current_year if end == "present" else int(end)
            if 1990 <= start_year <= current_year and start_year <= end_year:
                key = (start_year, end_year)
                if key not in seen:
                    seen.add(key)
                    total_months += (end_year - start_year) * 12
        except ValueError:
            continue

    return round(total_months / 12, 1)


# ── Keyword density ────────────────────────────────────────────────────────────

def count_keyword_matches(resume_text: str, keywords: list[str]) -> int:
    text_lower = resume_text.lower()
    return sum(1 for kw in keywords if kw.lower() in text_lower)


# ── Section detection ──────────────────────────────────────────────────────────

def detect_resume_sections(text: str) -> dict:
    text_lower = text.lower()
    section_keywords = {
        "has_summary": ["summary", "objective", "profile", "about"],
        "has_experience": ["experience", "work history", "employment"],
        "has_education": ["education", "degree", "university", "college"],
        "has_skills": ["skills", "technologies", "tools", "competencies"],
        "has_projects": ["projects", "portfolio", "work samples"],
        "has_certifications": ["certification", "certified", "certificate", "licence"],
    }

    sections = {}
    missing = []
    for key, keywords in section_keywords.items():
        found = any(kw in text_lower for kw in keywords)
        sections[key] = found
        if not found:
            missing.append(key.replace("has_", ""))

    sections["missing_sections"] = missing
    return sections


# ── Bullet analysis ────────────────────────────────────────────────────────────

def analyze_bullet(bullet: str) -> dict:
    score = 0
    issues = []
    suggestions = []

    words = bullet.strip().split()
    if not words:
        return {"bullet": bullet, "score": 0, "grade": "F", "issues": ["Empty bullet"], "suggestions": []}

    # 1. Starts with action verb (25pts)
    if words[0].lower().rstrip("eds") in [v.rstrip("eds") for v in ATS_POWER_WORDS]:
        score += 25
    else:
        issues.append("Doesn't start with a strong action verb")
        suggestions.append(f"Start with a power verb like: built, developed, led, optimized")

    # 2. Has quantified impact (35pts)
    if re.search(r'\d+', bullet):
        score += 35
    else:
        issues.append("No quantified impact")
        suggestions.append("Add metrics: % improvement, users affected, time saved, revenue impact")

    # 3. No weak words (20pts)
    weak_found = [w for w in WEAK_WORDS if w in bullet.lower()]
    if not weak_found:
        score += 20
    else:
        issues.append(f"Contains weak language: {', '.join(weak_found)}")
        suggestions.append("Replace weak phrases with direct action verbs")

    # 4. Appropriate length 10-30 words (20pts)
    word_count = len(words)
    if 10 <= word_count <= 30:
        score += 20
    elif word_count < 10:
        issues.append("Too short — add more detail and context")
    else:
        issues.append("Too long — consider splitting into two bullets")

    grade = "A" if score > 80 else "B" if score > 60 else "C" if score > 40 else "D"
    return {
        "bullet": bullet,
        "score": score,
        "grade": grade,
        "issues": issues,
        "suggestions": suggestions,
    }


# ── Main ATS scoring ───────────────────────────────────────────────────────────

def calculate_ats_score(
    resume_data: dict,
    jd_data: dict,
    resume_text: str,
) -> tuple[int, dict]:
    breakdown = {}

    # 1. Skills match (40%)
    required_skills = jd_data.get("required_skills", [])
    resume_skills = (
        resume_data.get("technical_skills", []) +
        resume_data.get("programming_languages", []) +
        resume_data.get("frameworks", []) +
        resume_data.get("tools", [])
    )

    matched_skills, missing_skills = [], []
    for skill in required_skills:
        if find_fuzzy_match(skill, resume_skills):
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    skills_score = (len(matched_skills) / max(len(required_skills), 1)) * 40
    breakdown["skills_match"] = round(skills_score)

    # 2. Experience match (25%)
    required_years = jd_data.get("required_years", 0) or 0
    resume_years = resume_data.get("total_experience", 0) or calculate_experience_years(resume_text)

    if required_years == 0:
        exp_score = 25
    elif resume_years >= required_years:
        exp_score = 25
    elif resume_years >= required_years * 0.7:
        exp_score = 15
    else:
        exp_score = 5
    breakdown["experience_match"] = exp_score

    # 3. Education match (15%)
    edu_score = match_education(
        jd_data.get("required_education", ""),
        resume_data.get("education", []),
    )
    breakdown["education_match"] = edu_score

    # 4. Keyword density (20%) — use only industry_keywords, not required_skills (already counted in skills)
    jd_keywords = list(set(jd_data.get("industry_keywords") or []))
    if not jd_keywords:
        jd_keywords = list(set(jd_data.get("required_skills") or []))
    keyword_hits = count_keyword_matches(resume_text, jd_keywords)
    keyword_score = min((keyword_hits / max(len(jd_keywords), 1)) * 20, 20)
    breakdown["keyword_density"] = round(keyword_score)

    total = sum(breakdown.values())
    return min(round(total), 100), breakdown


# ── Score card ─────────────────────────────────────────────────────────────────

def build_score_card(breakdown: dict, sections: dict, resume_years: float, required_years: float) -> dict:
    def grade(score, max_score):
        pct = score / max_score
        return "A" if pct >= 0.85 else "B" if pct >= 0.70 else "C" if pct >= 0.50 else "D"

    formatting_score = sum([
        sections.get("has_summary", False),
        sections.get("has_experience", False),
        sections.get("has_skills", False),
        sections.get("has_education", False),
        sections.get("has_projects", False),
    ])

    return {
        "skills": grade(breakdown.get("skills_match", 0), 40),
        "experience": grade(breakdown.get("experience_match", 0), 25),
        "education": grade(breakdown.get("education_match", 0), 15),
        "keywords": grade(breakdown.get("keyword_density", 0), 20),
        "formatting": grade(formatting_score, 5),
    }


# ── Quick wins ─────────────────────────────────────────────────────────────────

def generate_quick_wins(missing_skills: list, sections: dict, bullet_grades: list) -> list:
    wins = []

    for skill in missing_skills[:3]:
        wins.append(f"Add '{skill}' to your skills section if you have experience with it")

    for section in sections.get("missing_sections", [])[:2]:
        wins.append(f"Add a {section} section to your resume")

    poor_bullets = [b for b in bullet_grades if b["grade"] in ("C", "D")]
    if poor_bullets:
        wins.append("Quantify your bullet points with numbers and metrics")

    if not any(b["score"] >= 25 for b in bullet_grades):
        wins.append("Start bullet points with strong action verbs like 'Built', 'Led', 'Optimized'")

    return wins[:5]
