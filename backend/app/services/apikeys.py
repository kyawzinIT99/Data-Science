"""User API key management - allows users to bring their own OpenAI key."""

from app.core.database import db
from app.core.config import settings

keys_table = db.table("api_keys")


def save_user_api_key(api_key: str) -> None:
    """Save or update the user's custom API key."""
    keys_table.truncate()
    keys_table.insert({"openai_api_key": api_key})


def get_active_api_key() -> str:
    """Get the active API key - user's custom key or fallback to env."""
    docs = keys_table.all()
    if docs and docs[0].get("openai_api_key"):
        return docs[0]["openai_api_key"]
    return settings.OPENAI_API_KEY


def get_key_status() -> dict:
    """Get status of the current API key."""
    docs = keys_table.all()
    if docs and docs[0].get("openai_api_key"):
        key = docs[0]["openai_api_key"]
        return {"has_key": True, "key_preview": key[:8] + "..." + key[-4:]}
    if settings.OPENAI_API_KEY:
        key = settings.OPENAI_API_KEY
        return {"has_key": True, "key_preview": key[:8] + "..." + key[-4:]}
    return {"has_key": False, "key_preview": ""}


def remove_user_api_key() -> None:
    """Remove user's custom API key, reverting to env key."""
    keys_table.truncate()
