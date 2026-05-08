from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import create_tables
from app.routers import auth, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Створюємо таблиці при старті якщо не існують
    await create_tables()
    yield


app = FastAPI(
    title="GeoCenter Auth Service",
    description="Мікросервіс авторизації — реєстрація, логін, JWT токени, профіль",
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

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])


@app.get("/health")
async def health():
    """Health check — API Gateway пінгує цей ендпоінт."""
    return {"status": "ok", "service": "auth"}
