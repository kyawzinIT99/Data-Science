from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Setup logging
LOG_FILE = '/tmp/backend_error.log'
# Configure the parent 'app' logger so all routes (app.api...) and services (app.services...) inherit it
app_logger = logging.getLogger("app")
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
app_logger.addHandler(fh)
app_logger.setLevel(logging.DEBUG)

# Log startup
app_logger.info("Backend application starting...")

from app.core.config import settings
from app.api.routes import upload, analysis, chat, export, compare, cleaning, sharing, language, email_report, apikeys, forecast, causal, qa, refine, auth
from app.core.security import verify_token
from fastapi import Depends

app = FastAPI(
    title="AI Data Analysis Platform",
    description="Upload documents and analyze them with AI",
    version="1.0.0",
)

# Exception handlers... (already there, but I'll keep context)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "message": "Client Error"},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    app_logger.exception("Global exception caught")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "message": "Internal Server Error"},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Public Auth Route
app.include_router(auth.router, prefix="/api", tags=["Auth"])

# 2. Protected Data Routes
protected = [Depends(verify_token)]
app.include_router(upload.router, prefix="/api", tags=["Upload"], dependencies=protected)
app.include_router(analysis.router, prefix="/api", tags=["Analysis"], dependencies=protected)
app.include_router(chat.router, prefix="/api", tags=["Chat"], dependencies=protected)
app.include_router(export.router, prefix="/api", tags=["Export"], dependencies=protected)
app.include_router(compare.router, prefix="/api", tags=["Compare"], dependencies=protected)
app.include_router(cleaning.router, prefix="/api", tags=["Cleaning"], dependencies=protected)
app.include_router(language.router, prefix="/api", tags=["Language"], dependencies=protected)
app.include_router(email_report.router, prefix="/api", tags=["Email"], dependencies=protected)
app.include_router(apikeys.router, prefix="/api", tags=["Settings"], dependencies=protected)
app.include_router(forecast.router, prefix="/api", tags=["Forecasting"], dependencies=protected)
app.include_router(causal.router, prefix="/api", tags=["Causal"], dependencies=protected)
app.include_router(qa.router, prefix="/api", tags=["Quality"], dependencies=protected)
app.include_router(refine.router, prefix="/api", tags=["Refinement"], dependencies=protected)

# 3. Public Sharing Route (for recipients of shared links)
app.include_router(sharing.router, prefix="/api", tags=["Sharing"])


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# Mount the static frontend files
# We mount AFTER api routes to ensure /api/* takes precedence
STATIC_DIR = "/root/frontend_out"

@app.get("/{path:path}")
async def catch_all(path: str):
    # API routes are already handled by their specific routers above
    # We only handle frontend routes here
    
    # 1. Root redirect
    if not path or path == "/":
        return RedirectResponse(url="/en")
        
    # 2. Locale mapping (e.g. /en -> en.html)
    for locale in ["en", "th", "fr", "my"]:
        if path == locale or path == f"{locale}/":
            return FileResponse(f"{STATIC_DIR}/{locale}.html")
            
    # 3. Sharing view
    if path == "shared" or path.startswith("shared/"):
        return FileResponse(f"{STATIC_DIR}/shared.html")
        
    # 4. Static assets (_next, images, etc.)
    file_path = os.path.join(STATIC_DIR, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
        
    # 5. Fallback to 404 or default locale
    if os.path.exists(f"{STATIC_DIR}/404.html"):
        return FileResponse(f"{STATIC_DIR}/404.html")
    
    return RedirectResponse(url="/en")
