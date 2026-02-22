import logging
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

def is_modal_active() -> bool:
    """Check if Modal is enabled and the package is available."""
    if not settings.MODAL_ENABLED:
        return False
    try:
        import modal
        return True
    except ImportError:
        return False

def get_modal_func(func_name: str):
    """Dynamically lookup a Modal function if enabled."""
    if not settings.MODAL_ENABLED:
        return None
    try:
        import modal
        return modal.Function.from_name(settings.MODAL_APP_NAME, func_name)
    except Exception as e:
        logger.warning(f"Could not lookup Modal function {func_name}: {e}")
        return None

def sync_file_to_modal(file_id: str, file_path: str):
    """Ensure a file exists on the Modal Volume."""
    if not is_modal_active():
        return False
        
    try:
        check_func = get_modal_func("check_file_on_volume")
        save_func = get_modal_func("save_file_to_volume")
        
        if not check_func or not save_func:
            return False
            
        ext = os.path.splitext(file_path)[1].lower()
        if not check_func.remote(file_id, ext):
            logger.info(f"Uploading {file_id} to Modal Volume...")
            with open(file_path, "rb") as f:
                content = f.read()
            save_func.remote(file_id, ext, content)
            return True
        return True
    except Exception as e:
        logger.warning(f"Failed to sync file to Modal: {e}")
        return False
