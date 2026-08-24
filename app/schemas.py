from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class User_create(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "USER"

class Add_comment(BaseModel):
    ticket_id: int
    user_id: int
    content: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    role: str |None = None

class TicketCreate(BaseModel):
    title: str
    description: str
    user_id: int | None = None
    assigned_id: int | None = None
    category: str | None = None
    priority: str | None = None


class TicketUpdate(BaseModel):
    status: str | None = None
    category: str | None = None
    priority: str | None = None
    response: str | None = None
    assigned_id: int | None = None


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    user_id: int
    assigned_id: int | None = None
    response: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"