from datetime import datetime

from services.experience import calculate_experience, experience_section, required_years

NOW = datetime(2026, 11, 1)

RESUME = """Maridi Leela Akash
Education
KL University B.Tech CSE 2023 - 2027
Experience
Backend Intern, Acme
Jun 2025 - Aug 2025
Software Engineer, Beta
Jan 2026 - Present
Projects
Banking app 2024 - 2025
"""


def test_education_and_project_dates_are_ignored():
    section = experience_section(RESUME)
    assert "2023" not in section
    assert "Banking" not in section


def test_experience_counts_only_experience_section():
    result = calculate_experience(RESUME, now=NOW)
    # 2 months (Jun-Aug 2025) + 10 months (Jan-Nov 2026)
    assert result["total_years"] == 1.0
    assert result["periods"][-1]["end"] == "Present"


def test_no_experience_section_means_zero():
    assert calculate_experience("Education\nB.Tech 2023 - 2027", now=NOW)["total_years"] == 0.0


def test_overlapping_periods_merge():
    text = "Experience\nA 2020 - 2022\nB Jan 2021 - Dec 2021"
    assert calculate_experience(text, now=NOW)["total_years"] == 2.0


def test_future_end_dates_are_ignored():
    assert calculate_experience("Experience\nX 2025 - 2030", now=NOW)["total_years"] == 0.0


def test_required_years():
    assert required_years("We need 3+ years of experience in Java") == 3.0
    assert required_years("2-4 yrs of backend experience") == 2.0
    assert required_years("Freshers welcome") == 0.0
