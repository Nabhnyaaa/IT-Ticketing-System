from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from typing import Annotated, Literal

class Item(BaseModel):
    ID: int = 1
    Message: str = "Hello World"


app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def say_hello():
    return {"message": "Hello World"}

