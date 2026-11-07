import json
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import NotificationLog
from app.models.enums import NotificationChannel, NotificationStatus

class OutboxService:
    @staticmethod
    async def queue_notification(
        db: AsyncSession,
        user_id: int,
        template_name: str,
        payload: dict[str, Any],
        channel: NotificationChannel = NotificationChannel.EMAIL
    ) -> NotificationLog:
        """Enqueue notification in the same transaction as the triggering business action."""
        notification = NotificationLog(
            user_id=user_id,
            channel=channel,
            template_name=template_name,
            payload=json.dumps(payload),
            status=NotificationStatus.PENDING,
            retry_count=0,
            created_at=datetime.now(timezone.utc)
        )
        db.add(notification)
        return notification

    @staticmethod
    async def process_pending_notifications(
        db: AsyncSession,
        max_batch: int = 20,
        simulate_failure_for_test: bool = False
    ) -> list[NotificationLog]:
        """Processes pending notifications with retries and sanitized error recording."""
        query = (
            select(NotificationLog)
            .where(
                NotificationLog.status.in_([NotificationStatus.PENDING, NotificationStatus.FAILED]),
                NotificationLog.retry_count < 3
            )
            .order_by(NotificationLog.created_at.asc())
            .limit(max_batch)
        )
        result = await db.execute(query)
        items = result.scalars().all()

        for item in items:
            item.retry_count += 1
            item.last_attempt_at = datetime.now(timezone.utc)
            if simulate_failure_for_test:
                item.status = NotificationStatus.FAILED
                item.error_message = "Simulated delivery timeout (sanitized, no credentials)."
            else:
                # Simulated successful delivery (or integration with SMTP/SES in production)
                item.status = NotificationStatus.SENT
                item.error_message = None

        await db.commit()
        return list(items)
