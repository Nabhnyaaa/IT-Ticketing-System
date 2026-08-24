from fastapi import APIRouter
from .schemas import TicketCreate, TicketUpdate, TicketResponse, Add_comment
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .tasks import send_notification, deletion_notif_ticket
from .models import Ticket, Comment, User
from .auth import get_current_user, require_role


router = APIRouter(prefix="/tickets", tags=["Tickets"])

# will later alow users to create tickets in the frontend
@router.post("/create-ticket/")
async def create_ticket(
    log_ticket: TicketCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_ticket = Ticket(
        title=log_ticket.title,
        description=log_ticket.description,
        user_id=current_user.id,
        assigned_id=log_ticket.assigned_id if current_user.role.upper() in {"HELPDESK TECHNICIAN", "HELPDESK MANAGER", "ADMIN"} else None,
        category=log_ticket.category,
        priority=log_ticket.priority,
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
    current_user: User = Depends(get_current_user),
):
    query = select(Ticket)
    if current_user.role.upper() == "USER":
        query = query.where(Ticket.user_id == current_user.id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )
    if current_user.role.upper() == "USER" and ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own tickets")
    return ticket

# Updating ticket status and response
@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["HELPDESK TECHNICIAN", "HELPDESK MANAGER", "ADMIN"])),
):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )

    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )
    if ticket_data.status is not None:
        ticket.status = ticket_data.status
    if ticket_data.response is not None:
        ticket.response = ticket_data.response
    if ticket_data.category is not None:
        ticket.category = ticket_data.category
    if ticket_data.priority is not None and current_user.role.upper() in {"HELPDESK MANAGER", "ADMIN"}:
        ticket.priority = ticket_data.priority
    if ticket_data.assigned_id is not None and current_user.role.upper() in {"HELPDESK MANAGER", "ADMIN", "HELPDESK TECHNICIAN"}:
        assigned_user = await db.get(User, ticket_data.assigned_id)
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")
        ticket.assigned_id = assigned_user.id
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"])),
):
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


#Adding comments to a ticket
@router.post("/{ticket_id}/comments")
async def create_comment(ticket_id: int, log_comment: Add_comment, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role.upper() == "USER" and ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only comment on your own tickets")
    new_comment = Comment(
        content=log_comment.content,
        user_id=current_user.id,
        ticket_id=ticket_id,
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment



#Viewing comments of a ticket
@router.get("/{ticket_id}/comments")
async def get_comments(ticket_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role.upper() == "USER" and ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view comments on your own tickets")
    result = await db.execute(
        select(Comment).where(Comment.ticket_id == ticket_id).order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()
    if not comments:
        raise HTTPException(
            status_code=404,
            detail="No comments found for this ticket",
        )
    return comments