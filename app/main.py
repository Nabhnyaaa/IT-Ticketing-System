from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from typing import Annotated
from . import tickets, users
from contextlib import asynccontextmanager
from .database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Hospital Facility Support System",
    description="Backend API for managing hospital facility support tickets.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(tickets.router)


@app.get("/")
async def Welcome_page():
    return {"message": "Welcome to the Hospital Facility Support System"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}