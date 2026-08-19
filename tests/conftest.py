import pytest_asyncio

from app.main import app
from app.database import engine  # Import your existing engine from database.py


# 1. Clean up the engine pool before & after every async test
@pytest_asyncio.fixture(autouse=True)
async def reset_db_engine():
    yield
    # Dispose of connection pool so it doesn't hold references to closed loops
    await engine.dispose()
