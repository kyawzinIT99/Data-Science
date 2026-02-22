import os
import sys
import logging
from app.utils.modal import get_modal_func, is_modal_active
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("modal_health_check")

def check_deployment():
    print("=== Modal Deployment Health Check ===")
    print(f"MODAL_ENABLED: {settings.MODAL_ENABLED}")
    print(f"MODAL_APP_NAME: {settings.MODAL_APP_NAME}")
    
    if not is_modal_active():
        print("❌ Modal is not active in settings or package missing.")
        return
        
    funcs = [
        "check_file_on_volume",
        "save_file_to_volume",
        "run_forecast",
        "run_segmentation",
        "run_agent_analysis",
        "run_data_merge",
        "run_data_audit"
    ]
    
    all_ok = True
    for f_name in funcs:
        func = get_modal_func(f_name)
        if func:
            print(f"✅ Function '{f_name}': Found and verified.")
        else:
            print(f"❌ Function '{f_name}': NOT FOUND. Ensure you have run 'modal deploy modal_app.py'.")
            all_ok = False
            
    if all_ok:
        print("\n🎉 Deployment looks healthy! All remote functions are accessible.")
    else:
        print("\n⚠️ Some functions are missing. Please redeploy with 'modal deploy modal_app.py'.")

if __name__ == "__main__":
    check_deployment()
