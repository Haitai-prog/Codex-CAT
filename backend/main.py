from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, engine
from api.projects import router as projects_router
from api.documents import router as documents_router
from api.segments import router as segments_router
from api.tm import router as tm_router
from api.translations import router as translations_router
from api.glossary import router as glossary_router

app = FastAPI(title="Codex CAT", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(segments_router)
app.include_router(tm_router)
app.include_router(glossary_router)
app.include_router(translations_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
