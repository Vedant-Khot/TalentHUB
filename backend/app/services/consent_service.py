from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import StudentConsent

class ConsentService:
    @staticmethod
    async def record_consent(
        db: AsyncSession,
        student_id: int,
        policy_version: str = "1.0",
        purpose: str = "PLACEMENT_DATA_PROCESSING",
        is_granted: bool = True
    ) -> StudentConsent:
        consent = StudentConsent(
            student_id=student_id,
            policy_version=policy_version,
            purpose=purpose,
            is_granted=is_granted,
            event_timestamp=datetime.now(timezone.utc)
        )
        db.add(consent)
        await db.commit()
        await db.refresh(consent)
        return consent

    @staticmethod
    async def has_active_consent(
        db: AsyncSession,
        student_id: int,
        purpose: str = "PLACEMENT_DATA_PROCESSING"
    ) -> bool:
        """Determines current consent status from the most recent event."""
        query = (
            select(StudentConsent)
            .where(
                StudentConsent.student_id == student_id,
                StudentConsent.purpose == purpose
            )
            .order_by(StudentConsent.event_timestamp.desc(), StudentConsent.id.desc())
            .limit(1)
        )
        result = await db.execute(query)
        latest = result.scalar_one_or_none()
        if not latest:
            return False
        return latest.is_granted
