from fastapi import FastAPI, APIRouter
from .schemas import User_create
from .tasks import send_notification_user
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db


router = APIRouter(prefix="/users", tags=["Users"])

# will later alow creation of users
@router.post("/create-user/")
async def create_user(user: User_create, db: AsyncSession = Depends(get_db)):
    new_user = User(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        password=user.password,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    background_tasks.add_task(
        send_notification_user,
        new_user.id,
    )
    return new_user



# will later show the users in the frontend as a table
@router.get("/users/{user_id}")
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return user