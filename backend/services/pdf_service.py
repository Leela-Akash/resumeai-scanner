import fitz
from services.analysis_service import detect_resume_sections


def extract_text(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return cleaned


def extract_text_with_sections(file_bytes: bytes) -> tuple[str, dict]:
    text = extract_text(file_bytes)
    sections = detect_resume_sections(text)
    return text, sections
