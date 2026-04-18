import fitz


def extract_text(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return cleaned
