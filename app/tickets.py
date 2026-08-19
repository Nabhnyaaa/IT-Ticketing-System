from fastapi import APIRouter
from .schemas import TicketCreate, TicketUpdate, TicketResponse
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .tasks import send_notification, deletion_notif_ticket
from .models import Ticket

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# will later alow users to create tickets in the frontend
@router.post("/create-ticket/")
async def create_ticket(log_ticket: TicketCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    new_ticket = Ticket(
        title=log_ticket.title,
        description=log_ticket.description,
        user_id=log_ticket.user_id,
        status="OPEN",
    )

    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)

    background_tasks.add_task(
        send_notification,
        new_ticket.id,
    )
    return new_ticket



# will later show the tickets in the frontend as a table
@router.get("/", response_model=list[TicketResponse])
async def get_tickets(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Ticket))
    return result.scalars().all()


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db),):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )
    return ticket

# Updating ticket status and response
@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(ticket_id: int, ticket_data: TicketUpdate, db: AsyncSession = Depends(get_db),):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )

    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )
    ticket.status = ticket_data.status
    ticket.response = ticket_data.response
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db),):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )
    background_tasks.add_task(
        deletion_notif_ticket,
        ticket.id
    )

    await db.delete(ticket)
    await db.commit()
    return {"message": "Ticket deleted successfully"}