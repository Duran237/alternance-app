from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routers import auth, users, cv, jobs, applications, stats
from routers import automation
from services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Alternance App API",
    description="Application intelligente de recherche d'alternance",
    version="1.0.0",
    lifespan=lifespan,
)

_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    settings.FRONTEND_URL,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(cv.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(stats.router)
app.include_router(automation.router)


@app.get("/")
async def root():
    return {"message": "Alternance App API v1.0", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
