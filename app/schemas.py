from datetime import datetime
from pydantic import BaseModel


class User_create(BaseModel):
    name: str
    email: str
    password: str

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None

class TicketCreate(BaseModel):
    title: str
    description: str
    user_id: int


class TicketUpdate(BaseModel):
    status: str
    response: str | None = None


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    user_id: int
    response: str | None
    created_at: datetime
    updated_at: datetime
