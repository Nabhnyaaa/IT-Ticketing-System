from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from . import auth_routes, tickets, users
import app.models
from contextlib import asynccontextmanager
from .database import Base, engine
import json
import logging
# study sso and cognito
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="IT Ticketing System",
    description="Backend API for managing IT support tickets.",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(auth_routes.router)
app.include_router(users.router)
app.include_router(tickets.router)
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/")
async def Welcome_page():
    return {"message": "Welcome to the IT Ticketting System"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}



@app.middleware("http")
async def hide_user_pass(request: Request, call_next):
    response = await call_next(request)
    logging.info("Entered middleware")
    if request.url.path.startswith("/tickets"):
        return response
    # Only process JSON responses
    if request.method == "GET" and "application/json" in response.headers.get("content-type", ""):
        body = b""
        logging.info("Processing JSON response for user retrieval")
        async for chunk in response.body_iterator:
            body += chunk
        try:
            data = json.loads(body.decode("utf-8"))
            # Hide password in single object
            if isinstance(data, dict) and "password" in data:
                logging.info("Its a dict object, hiding password")
                data["password"] = "#" * len(data.get("password", ""))
            # Hide password in list of objects
            elif isinstance(data, list):
                logging.info("Its a list object, hiding passwords")
                for item in data:
                    if isinstance(item, dict) and "password" in item:
                        item["password"] = "#" * len(item.get("password", ""))
            logging.info("Password successfully hidden in response")
            # Return modified response
            return JSONResponse(
                content=data,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            logging.error(f"Error processing response: {str(e)}", exc_info=True)
            # If JSON parsing fails, return original response
            return JSONResponse(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
    return response