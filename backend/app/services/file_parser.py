import os
import uuid
import pandas as pd
from pypdf import PdfReader
from docx import Document
from pathlib import Path
import logging

# Setup explicit file logging
LOG_FILE = '/tmp/backend_error.log'
logger = logging.getLogger(__name__)
if not logger.handlers:
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.setLevel(logging.ERROR)

from app.core.config import settings
from app.services.ocr import ocr_pdf, ocr_image, needs_ocr, is_ocr_available


SUPPORTED_EXTENSIONS = {
    ".csv", ".xlsx", ".xls", ".pdf", ".docx", ".txt", ".json",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp",
}


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_file(filename: str, file_size: int) -> tuple[bool, str]:
    ext = get_file_extension(filename)
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
    return True, ""


def save_uploaded_file(file_content: bytes, filename: str) -> tuple[str, str]:
    file_id = str(uuid.uuid4())
    ext = get_file_extension(filename)
    save_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(file_content)
    return file_id, save_path


async def save_uploaded_file_stream(file, filename: str) -> tuple[str, str]:
    """Save a FastAPI UploadFile stream to disk in chunks to save memory."""
    import aiofiles
    file_id = str(uuid.uuid4())
    ext = get_file_extension(filename)
    save_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    async with aiofiles.open(save_path, "wb") as f:
        while chunk := await file.read(1024 * 1024): # 1MB chunks
            await f.write(chunk)
            
    return file_id, save_path


def extract_text(file_path: str) -> str:
    ext = get_file_extension(file_path)

    try:
        if ext == ".pdf":
            text = _extract_pdf(file_path)
            if needs_ocr(file_path, text) and is_ocr_available():
                try:
                    ocr_text = ocr_pdf(file_path)
                    if len(ocr_text) > len(text):
                        return ocr_text
                except Exception:
                    pass  # OCR failed, fall back to normal text
            return text
        elif ext in (".xlsx", ".xls"):
            return _extract_excel(file_path)
        elif ext == ".csv":
            return _extract_csv(file_path)
        elif ext == ".docx":
            return _extract_docx(file_path)
        elif ext == ".txt":
            return _extract_txt(file_path)
        elif ext == ".json":
            return _extract_json(file_path)
        elif ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
            return _extract_image(file_path)
        else:
            return f"[Unsupported file type: {ext}]"
    except Exception as e:
        return f"[Error extracting text from {ext} file: {str(e)}]"


def extract_dataframe(file_path: str) -> pd.DataFrame | None:
    ext = get_file_extension(file_path)
    try:
        if ext == ".csv":
            return pd.read_csv(file_path)
        elif ext in (".xlsx", ".xls"):
            try:
                # Try default auto-detect
                return pd.read_excel(file_path)
            except Exception:
                try:
                    # Try openpyxl
                    return pd.read_excel(file_path, engine='openpyxl')
                except Exception:
                    # Try xlrd (older .xls)
                    return pd.read_excel(file_path, engine='xlrd')
        elif ext == ".json":
            return pd.read_json(file_path)
    except Exception as e:
        logger.error(f"Failed to extract dataframe from {file_path}: {e}")
        return None
    return None


def _extract_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n\n".join(text_parts)


def _extract_excel(file_path: str) -> str:
    try:
        try:
            df = pd.read_excel(file_path)
        except Exception:
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
            except Exception:
                df = pd.read_excel(file_path, engine='xlrd')
        
        return f"Columns: {', '.join(df.columns.tolist())}\n\n{df.to_string(max_rows=200)}"
    except Exception as e:
        return f"[Excel Parsing Error: {str(e)}]"


def _extract_csv(file_path: str) -> str:
    try:
        # Try default (UTF-8)
        df = pd.read_csv(file_path)
    except UnicodeDecodeError:
        try:
            # Try common fallback encodings
            df = pd.read_csv(file_path, encoding='latin1')
        except Exception as e:
            return f"[CSV Parsing Error: {str(e)}]"
    except Exception as e:
        return f"[CSV Parsing Error: {str(e)}]"
        
    return f"Columns: {', '.join(df.columns.tolist())}\n\n{df.to_string(max_rows=200)}"


def _extract_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())


def _extract_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _extract_json(file_path: str) -> str:
    import json
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, indent=2)[:50000]


def _extract_image(file_path: str) -> str:
    try:
        text = ocr_image(file_path)
        if text and text.strip():
            return text
    except Exception:
        pass
    return "[Image file - no text could be extracted via OCR]"
