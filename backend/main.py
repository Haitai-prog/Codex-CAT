import os, webbrowser, threading
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db
from api.projects import router as projects_router
from api.documents import router as documents_router
from api.segments import router as segments_router
from api.tm import router as tm_router
from api.translations import router as translations_router
from api.glossary import router as glossary_router
from api.glossary_import import router as glossary_import_router

app = FastAPI(title="Codex CAT", version="0.2.0")
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "frontend" / "dist"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(segments_router)
app.include_router(tm_router)
app.include_router(glossary_router)
app.include_router(glossary_import_router)
app.include_router(translations_router)


@app.on_event("startup")
def on_startup():
    init_db()
    threading.Thread(target=_open_browser, daemon=True).start()


def _open_browser():
    import time
    time.sleep(1.0)
    webbrowser.open("http://localhost:8080")


@app.get("/api/health")
def health():
    return {"status": "ok"}


if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        fp = STATIC_DIR / (full_path or "index.html")
        if fp.exists() and not fp.is_dir():
            return FileResponse(str(fp))
        return FileResponse(str(STATIC_DIR / "index.html"))
else:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
