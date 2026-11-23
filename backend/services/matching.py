"""Keyword matching between a job description and a resume.

The old matcher used rapidfuzz.partial_ratio >= 85, which treats "Java" as a match for
"JavaScript" (partial_ratio = 100) and "SQL" for "NoSQL". This module matches on
normalised forms, known aliases and whole-token fuzzy similarity instead.
"""
import re

from rapidfuzz import fuzz

# Canonical name -> spellings that mean the same thing.
_ALIASES: dict[str, set[str]] = {
    "javascript": {"js", "javascript", "ecmascript", "es6"},
    "typescript": {"ts", "typescript"},
    "node": {"node", "nodejs", "node.js"},
    "react": {"react", "reactjs", "react.js"},
    "next": {"next", "nextjs", "next.js"},
    "vue": {"vue", "vuejs", "vue.js"},
    "postgresql": {"postgres", "postgresql", "psql"},
    "kubernetes": {"kubernetes", "k8s"},
    "aws": {"aws", "amazon web services"},
    "gcp": {"gcp", "google cloud", "google cloud platform"},
    "ci/cd": {"ci/cd", "cicd", "ci cd", "continuous integration"},
    "rest": {"rest", "rest api", "rest apis", "restful", "restful api", "restful apis"},
    "machine learning": {"ml", "machine learning"},
    "spring boot": {"spring boot", "springboot"},
    "golang": {"go", "golang"},
}
_ALIAS_LOOKUP = {spelling: canon for canon, spellings in _ALIASES.items() for spelling in spellings}

# A resume skill on the right also proves the broader JD skill on the left.
_IMPLIES: dict[str, set[str]] = {
    "sql": {"mysql", "postgresql", "sqlite", "sql server", "oracle", "mariadb", "dbms"},
    "api design": {"rest", "graphql", "fastapi", "spring boot", "express"},
    "rest api": {"rest"},
    "javascript": {"typescript", "react", "node"},
    "cloud": {"aws", "gcp", "azure"},
    "containers": {"docker", "kubernetes"},
    "version control": {"git", "github"},
}


def normalize(keyword: str) -> str:
    k = keyword.lower().strip()
    k = re.sub(r"\s+", " ", k)
    k = k.strip(" .,;:")
    return _ALIAS_LOOKUP.get(k, k)


def keywords_match(jd_kw: str, resume_kw: str) -> bool:
    a, b = normalize(jd_kw), normalize(resume_kw)
    if a == b or b in _IMPLIES.get(a, set()):
        return True
    # Very short skills (Go, C, R, SQL, AWS) must match exactly; fuzzy matching them is noise.
    if min(len(a), len(b)) <= 4:
        return False
    # token_set_ratio compares whole words, so "Java" vs "JavaScript" scores low
    # while "Microsoft Azure" vs "Azure" or "unit testing" vs "unit tests" score high.
    return fuzz.token_set_ratio(a, b) >= 90


def match_keywords(jd_keywords: list[str], resume_keywords: list[str], resume_text: str = "") -> dict:
    """Split JD keywords into matched / missing. Also counts a keyword as matched when it
    appears verbatim (word-bounded) in the resume text, which catches skills the
    extraction step missed."""
    text = resume_text.lower()
    matched: list[str] = []
    missing: list[str] = []
    seen: set[str] = set()
    for kw in jd_keywords:
        key = normalize(kw)
        if key in seen:
            continue
        seen.add(key)
        in_list = any(keywords_match(kw, r) for r in resume_keywords)
        in_text = bool(text) and re.search(rf"(?<![\w.+#]){re.escape(kw.lower())}(?![\w+#])", text) is not None
        (matched if in_list or in_text else missing).append(kw)
    total = len(matched) + len(missing)
    pct = round(len(matched) / total * 100, 1) if total else 0.0
    return {"matched_keywords": matched, "missing_keywords": missing, "match_percentage": pct}


def _spellings(canonical: str) -> set[str]:
    return _ALIASES.get(canonical, set()) | {canonical}


def mentions_skill(text: str, jd_keyword: str) -> bool:
    """True if the text names the skill, an alias of it, or a more specific skill that proves it
    (e.g. "REST APIs" for "API design", "MySQL" for "SQL")."""
    canon = normalize(jd_keyword)
    terms = {jd_keyword.lower()} | _spellings(canon)
    for implied in _IMPLIES.get(canon, set()):
        terms |= _spellings(implied)
    low = text.lower()
    return any(re.search(rf"(?<![\w.+#]){re.escape(t)}(?![\w+#])", low) for t in terms)
