from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import create_tables
from app.routers import analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="GeoCenter Analytics Service",
    description="Мікросервіс аналітики — статистика, K-Means кластеризація, heatmap, відстані",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "analytics"}
