import fitz

MAX_PAGES = 5
MIN_TEXT_CHARS = 200


class PDFError(Exception):
    """User-facing problem with the uploaded PDF."""


def extract_text(file_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception:
        raise PDFError("Could not read this PDF. Try exporting it again.")
    try:
        if doc.needs_pass:
            raise PDFError("This PDF is password-protected. Remove the password and upload again.")
        if doc.page_count > MAX_PAGES:
            raise PDFError(f"Resume is {doc.page_count} pages. Upload a resume of {MAX_PAGES} pages or fewer.")
        text = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()

    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(cleaned) < MIN_TEXT_CHARS:
        raise PDFError(
            "We couldn't find text in this PDF. It may be a scanned image. "
            "Export your resume as a text-based PDF and try again."
        )
    return cleaned
