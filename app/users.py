from fastapi import APIRouter
from .schemas import User_create, UserUpdate
from .tasks import send_notification_user, deletion_notif_user
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .models import User

router = APIRouter(prefix="/users", tags=["Users"])


# will later show the users in the frontend as a table
@router.get("/")
async def read_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users



# will later alow creation of users
@router.post("/create-user/")
async def create_user(user: User_create, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    new_user = User(
        name=user.name,
        email=user.email,
        password=user.password
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    background_tasks.add_task(
        send_notification_user,
        new_user.id,
    )
    return new_user


# will later show the user in the frontend as a table
@router.get("/{user_id}")
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



# Updating existing user details
@router.put("/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.password is not None:
        user.password = user_data.password
    await db.commit()
    await db.refresh(user)
    return user

#delete endpoint used to delete a user from the database
@router.delete("/{user_id}")
async def delete_user(user_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    background_tasks.add_task(
        deletion_notif_user,
        user.id
    )
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}