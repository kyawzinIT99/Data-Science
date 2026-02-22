import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./.storage/uploads")
    VECTORSTORE_DIR: str = os.getenv("VECTORSTORE_DIR", "./.storage/vectorstore")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHAT_MODEL: str = "gpt-4o"
    ANALYSIS_MODEL: str = "gpt-4o"
    SHARE_BASE_URL: str = os.getenv("SHARE_BASE_URL", "http://localhost:3000/shared")
    MODAL_ENABLED: bool = os.getenv("MODAL_ENABLED", "false").lower() == "true"
    MODAL_APP_NAME: str = os.getenv("MODAL_APP_NAME", "ai-data-analysis")
    # Email settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")


settings = Settings()
