"""OCR service for scanned PDFs and images using Tesseract."""

import io
from PIL import Image

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


def is_ocr_available() -> bool:
    return TESSERACT_AVAILABLE and PDF2IMAGE_AVAILABLE


def ocr_pdf(file_path: str) -> str:
    """Extract text from a scanned PDF using OCR."""
    if not is_ocr_available():
        return ""

    pages = convert_from_path(file_path, dpi=300)
    text_parts = []

    for i, page_img in enumerate(pages):
        text = pytesseract.image_to_string(page_img)
        if text.strip():
            text_parts.append(f"--- Page {i + 1} ---\n{text.strip()}")

    return "\n\n".join(text_parts)


def ocr_image(file_path: str) -> str:
    """Extract text from an image file using OCR."""
    if not TESSERACT_AVAILABLE:
        return ""

    img = Image.open(file_path)
    return pytesseract.image_to_string(img)


def needs_ocr(file_path: str, extracted_text: str) -> bool:
    """Check if a PDF likely needs OCR (very little text extracted normally)."""
    if not file_path.lower().endswith(".pdf"):
        return False
    # If normal extraction got very little text, try OCR
    stripped = extracted_text.strip()
    return len(stripped) < 50
