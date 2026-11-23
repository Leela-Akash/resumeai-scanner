from services.matching import keywords_match, match_keywords, normalize


def test_java_is_not_javascript():
    assert not keywords_match("Java", "JavaScript")
    assert not keywords_match("JavaScript", "Java")


def test_sql_is_not_nosql():
    assert not keywords_match("SQL", "NoSQL")


def test_aliases():
    assert keywords_match("Node.js", "NodeJS")
    assert keywords_match("Postgres", "PostgreSQL")
    assert keywords_match("K8s", "Kubernetes")
    assert keywords_match("RESTful APIs", "REST API")


def test_whole_word_fuzzy():
    assert keywords_match("Microsoft Azure", "Azure")
    assert keywords_match("Data Structures", "Data Structures and Algorithms")
    assert keywords_match("Spring Boot", "SpringBoot")


def test_short_skills_need_exact_match():
    assert not keywords_match("Go", "Google")
    assert keywords_match("Go", "Golang")


def test_match_dedupes_and_uses_text_fallback():
    result = match_keywords(
        ["React", "react", "Docker", "Kafka", "C++"],
        ["React.js"],
        resume_text="Built services with Docker and C++",
    )
    assert result["matched_keywords"] == ["React", "Docker", "C++"]
    assert result["missing_keywords"] == ["Kafka"]
    assert result["match_percentage"] == 75.0


def test_text_fallback_respects_word_boundaries():
    result = match_keywords(["Java"], [], resume_text="Skilled in JavaScript")
    assert result["missing_keywords"] == ["Java"]


def test_empty_jd_keywords():
    assert match_keywords([], ["React"])["match_percentage"] == 0.0


def test_normalize():
    assert normalize("  React.js ") == "react"
