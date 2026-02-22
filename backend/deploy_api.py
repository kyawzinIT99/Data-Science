import modal
import os

# Define the image with all necessary dependencies
image = (
    modal.Image.debian_slim()
    .pip_install_from_requirements("requirements.txt")
    .pip_install(
        "pandas",
        "numpy",
        "scikit-learn",
        "hdbscan",
        "prophet",
        "statsmodels",
        "openai",
        "pydantic",
        "networkx",
        "pingouin",
        "openpyxl",
        "aiofiles",
        "python-jose[cryptography]"
    )
    .env({
        "UPLOAD_DIR": "/data/uploads",
        "VECTORSTORE_DIR": "/data/vectorstore",
        "MODAL_ENABLED": "true",
        "MODAL_APP_NAME": "ai-data-analysis",
        "SHARE_BASE_URL": "https://kyawzin-ccna--ai-data-analysis-web-v4-web-app.modal.run/shared",
        "ALLOWED_ORIGINS": "*",
        "PYTHONPATH": "/root",
    })
    .add_local_dir(
        os.path.join(os.path.dirname(__file__), "app"),
        remote_path="/root/app"
    )
    .add_local_dir(
        os.path.join(os.path.dirname(__file__), "../frontend/out"),
        remote_path="/root/frontend_out"
    )
)

# Persistent volume for data storage (same as used in modal_app.py)
volume = modal.Volume.from_name("data-analysis-storage", create_if_missing=True)

app = modal.App("ai-data-analysis-web-v4")

@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-api-key")],
    timeout=600,
    scaledown_window=300,
)
@modal.asgi_app()
def web_app():
    # Ensure directories exist on volume BEFORE importing app
    os.makedirs("/data/uploads", exist_ok=True)
    os.makedirs("/data/vectorstore", exist_ok=True)

    from app.main import app as fastapi_app
    return fastapi_app
