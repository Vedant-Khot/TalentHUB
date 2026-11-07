import uuid
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import (
    Application, InterviewSlot, Offer, Student, JobListing,
    ApplicationStatusHistory
)
from app.models.enums import (
    ApplicationStage, InterviewStatus, InterviewResult, OfferStatus
)
from app.services.outbox_service import OutboxService
from app.core.config import settings

class InterviewService:
    @staticmethod
    async def schedule_round(
        db: AsyncSession,
        application_id: int,
        round_number: int,
        scheduled_time: datetime,
        venue_or_link: str,
        actor_user_id: int,
        notes: Optional[str] = None
    ) -> InterviewSlot:
        """Schedules an interview round. Application must be SHORTLISTED or already in interview stage."""
        app_query = select(Application).where(Application.id == application_id)
        res = await db.execute(app_query)
        application = res.scalar_one_or_none()
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        if application.stage not in [ApplicationStage.SHORTLISTED, ApplicationStage.INTERVIEW_SCHEDULED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot schedule interview when application is in {application.stage} stage."
            )

        # Check existing round
        existing_round_query = select(InterviewSlot).where(
            InterviewSlot.application_id == application_id,
            InterviewSlot.round_number == round_number
        )
        existing_res = await db.execute(existing_round_query)
        if existing_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Interview round {round_number} is already scheduled for this application."
            )

        slot = InterviewSlot(
            application_id=application_id,
            round_number=round_number,
            scheduled_time=scheduled_time,
            venue_or_link=venue_or_link,
            status=InterviewStatus.SCHEDULED,
            result=InterviewResult.PENDING,
            notes=notes
        )
        db.add(slot)

        # Update application stage to INTERVIEW_SCHEDULED if not already
        if application.stage != ApplicationStage.INTERVIEW_SCHEDULED:
            application.stage = ApplicationStage.INTERVIEW_SCHEDULED
            history = ApplicationStatusHistory(
                application_id=application.id,
                from_stage=ApplicationStage.SHORTLISTED,
                to_stage=ApplicationStage.INTERVIEW_SCHEDULED,
                changed_by_user_id=actor_user_id,
                reason=f"Interview round {round_number} scheduled.",
                changed_at=datetime.now(timezone.utc)
            )
            db.add(history)

        await db.commit()
        await db.refresh(slot)
        return slot

    @staticmethod
    async def reschedule_round(
        db: AsyncSession,
        slot_id: int,
        new_time: datetime,
        venue_or_link: Optional[str] = None,
        notes: Optional[str] = None
    ) -> InterviewSlot:
        """Safely reschedules an existing interview round."""
        slot = await db.get(InterviewSlot, slot_id)
        if not slot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview slot not found.")

        slot.scheduled_time = new_time
        if venue_or_link:
            slot.venue_or_link = venue_or_link
        if notes:
            slot.notes = notes
        slot.status = InterviewStatus.RESCHEDULED

        await db.commit()
        await db.refresh(slot)
        return slot

    @staticmethod
    async def record_result(
        db: AsyncSession,
        slot_id: int,
        result: InterviewResult,
        actor_user_id: int,
        notes: Optional[str] = None,
        mark_all_rounds_complete: bool = False
    ) -> InterviewSlot:
        """Records interview result (PASSED / FAILED). If all rounds complete, transitions to INTERVIEWED."""
        slot = await db.get(InterviewSlot, slot_id)
        if not slot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview slot not found.")

        slot.result = result
        slot.status = InterviewStatus.COMPLETED
        if notes:
            slot.notes = notes

        if mark_all_rounds_complete and result == InterviewResult.PASSED:
            application = await db.get(Application, slot.application_id)
            if application and application.stage == ApplicationStage.INTERVIEW_SCHEDULED:
                application.stage = ApplicationStage.INTERVIEWED
                history = ApplicationStatusHistory(
                    application_id=application.id,
                    from_stage=ApplicationStage.INTERVIEW_SCHEDULED,
                    to_stage=ApplicationStage.INTERVIEWED,
                    changed_by_user_id=actor_user_id,
                    reason=f"Interview rounds passed. Marked INTERVIEWED.",
                    changed_at=datetime.now(timezone.utc)
                )
                db.add(history)

        await db.commit()
        await db.refresh(slot)
        return slot


class OfferService:
    @staticmethod
    async def create_offer(
        db: AsyncSession,
        application_id: int,
        package_lpa: float,
        actor_user_id: int,
        acceptance_deadline: Optional[datetime] = None
    ) -> Offer:
        """
        Creates an offer for an INTERVIEWED application.
        Transitions application to OFFERED.
        Generates private offer letter storage key and mock document.
        """
        app_query = (
            select(Application)
            .options(selectinload(Application.student), selectinload(Application.job))
            .where(Application.id == application_id)
        )
        res = await db.execute(app_query)
        application = res.scalar_one_or_none()
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        if application.stage != ApplicationStage.INTERVIEWED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot issue offer to an application in {application.stage} stage. Application must be INTERVIEWED."
            )

        # Check existing offer
        existing_offer_query = select(Offer).where(Offer.application_id == application_id)
        existing_res = await db.execute(existing_offer_query)
        if existing_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An offer has already been issued for this application."
            )

        storage_key = f"offer_{uuid.uuid4().hex}"
        
        # Write dummy offer letter content to private storage
        file_path = os.path.join(settings.OFFERS_STORAGE_DIR, f"{storage_key}.pdf")
        os.makedirs(settings.OFFERS_STORAGE_DIR, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(
                f"%PDF-1.4 TalentHub Confidential Offer Letter for {application.student.full_name} ({application.student.usn}) - Package: {package_lpa} LPA".encode()
            )

        offer = Offer(
            application_id=application_id,
            package_lpa=package_lpa,
            issue_date=datetime.now(timezone.utc),
            acceptance_deadline=acceptance_deadline,
            letter_storage_key=storage_key,
            status=OfferStatus.PENDING
        )
        db.add(offer)

        # Transition application to OFFERED
        application.stage = ApplicationStage.OFFERED
        history = ApplicationStatusHistory(
            application_id=application.id,
            from_stage=ApplicationStage.INTERVIEWED,
            to_stage=ApplicationStage.OFFERED,
            changed_by_user_id=actor_user_id,
            reason=f"Offer extended with package {package_lpa} LPA.",
            changed_at=datetime.now(timezone.utc)
        )
        db.add(history)

        # Enqueue notification
        await OutboxService.queue_notification(
            db=db,
            user_id=application.student.user_id,
            template_name="OFFER_EXTENDED",
            payload={"application_id": application.id, "package_lpa": package_lpa}
        )

        await db.commit()
        await db.refresh(offer)
        return offer

    @staticmethod
    async def respond_to_offer(
        db: AsyncSession,
        offer_id: int,
        student_user_id: int,
        action: str  # ACCEPT or DECLINE
    ) -> Offer:
        """
        Processes offer acceptance or decline by student.
        Enforces:
        - Authenticated student ownership
        - Season-aware single accepted offer guarantee
        """
        offer_query = (
            select(Offer)
            .options(
                selectinload(Offer.application).selectinload(Application.student),
                selectinload(Offer.application).selectinload(Application.job)
            )
            .where(Offer.id == offer_id)
        )
        res = await db.execute(offer_query)
        offer = res.scalar_one_or_none()
        if not offer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")

        application = offer.application
        student = application.student

        # Verify Student Ownership
        if student.user_id != student_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to respond to this offer."
            )

        if offer.status != OfferStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Offer has already been {offer.status}."
            )

        action_upper = action.upper()
        if action_upper == "ACCEPT":
            # Check season-aware rule: has student already accepted an offer in this season?
            season_id = application.job.season_id
            existing_accepted_query = (
                select(Offer)
                .join(Application, Offer.application_id == Application.id)
                .join(JobListing, Application.job_id == JobListing.id)
                .where(
                    Application.student_id == student.id,
                    JobListing.season_id == season_id,
                    Offer.status == OfferStatus.ACCEPTED
                )
            )
            existing_accepted_res = await db.execute(existing_accepted_query)
            if existing_accepted_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already accepted an offer in this placement season. A student cannot accept more than one offer per season."
                )

            offer.status = OfferStatus.ACCEPTED
            offer.response_timestamp = datetime.now(timezone.utc)
            application.stage = ApplicationStage.ACCEPTED

            history = ApplicationStatusHistory(
                application_id=application.id,
                from_stage=ApplicationStage.OFFERED,
                to_stage=ApplicationStage.ACCEPTED,
                changed_by_user_id=student_user_id,
                reason="Offer accepted by student.",
                changed_at=datetime.now(timezone.utc)
            )
            db.add(history)

        elif action_upper == "DECLINE":
            offer.status = OfferStatus.DECLINED
            offer.response_timestamp = datetime.now(timezone.utc)

            history = ApplicationStatusHistory(
                application_id=application.id,
                from_stage=ApplicationStage.OFFERED,
                to_stage=ApplicationStage.OFFERED,
                changed_by_user_id=student_user_id,
                reason="Offer declined by student.",
                changed_at=datetime.now(timezone.utc)
            )
            db.add(history)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be either ACCEPT or DECLINE."
            )

        await db.commit()
        await db.refresh(offer)
        return offer
