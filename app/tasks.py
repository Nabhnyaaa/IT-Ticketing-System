import logging

logger = logging.getLogger(__name__)


async def send_notification(ticket_id: int):
    logger.info(
        "Notification: New ticket created - Ticket ID: %s",
        ticket_id,
    )


async def send_notification_user(user_id: int):
    logger.info(
        "Notification: New user created - User ID: %s",
        user_id,
    )