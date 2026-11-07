from datetime import datetime, timezone
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import (
    Application, ApplicationStatusHistory, JobListing, Student,
    InterviewSlot, Offer, User
)
from app.models.enums import (
    ApplicationStage, JobStatus, InterviewStatus,
    InterviewResult, OfferStatus, UserRole
)
from app.services.eligibility_service import EligibilityService
from app.services.consent_service import ConsentService
from app.services.outbox_service import OutboxService

VALID_TRANSITIONS = {
    ApplicationStage.APPLIED: [ApplicationStage.SHORTLISTED],
    ApplicationStage.SHORTLISTED: [ApplicationStage.INTERVIEW_SCHEDULED],
    ApplicationStage.INTERVIEW_SCHEDULED: [ApplicationStage.INTERVIEWED],
    ApplicationStage.INTERVIEWED: [ApplicationStage.OFFERED],
    ApplicationStage.OFFERED: [ApplicationStage.ACCEPTED]
}

class ApplicationService:
    @staticmethod
    async def apply_to_job(
        db: AsyncSession,
        student_id: int,
        job_id: int,
        actor_user_id: int
    ) -> Application:
        """
        Creates an application while enforcing:
        - Student consent
        - Drive publication status
        - Deterministic real-time eligibility check
        - Duplicate application prevention
        - Same company, same season lockout across any job
        """
        # 1. Fetch Student & Job
        student = await db.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

        job = await db.get(JobListing, job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job drive not found.")

        # 2. Check Drive Status
        if job.status != JobStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job drive is currently {job.status}. Applications are only accepted for PUBLISHED drives."
            )

        # 3. Check Consent
        has_consent = await ConsentService.has_active_consent(db, student_id)
        if not has_consent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Active data processing consent is required to apply for campus drives."
            )

        # 4. Check Duplicate Application to same job
        existing_app_query = select(Application).where(
            Application.student_id == student_id,
            Application.job_id == job_id
        )
        existing_app_res = await db.execute(existing_app_query)
        if existing_app_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied to this job listing."
            )

        # 5. Check Same Company, Same Season Lockout
        same_company_season_query = (
            select(Application)
            .join(JobListing, Application.job_id == JobListing.id)
            .where(
                Application.student_id == student_id,
                JobListing.company_id == job.company_id,
                JobListing.season_id == job.season_id
            )
        )
        same_company_res = await db.execute(same_company_season_query)
        if same_company_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied to this company in this placement season."
            )

        # 6. Revalidate Eligibility Engine
        eval_result = await EligibilityService.evaluate_eligibility(
            db=db,
            student=student,
            job=job,
            persist_decision=True
        )
        if not eval_result["is_eligible"]:
            # Record notification for ineligibility
            await OutboxService.queue_notification(
                db=db,
                user_id=student.user_id,
                template_name="INELIGIBILITY_NOTICE",
                payload={"job_id": job.id, "reasons": eval_result["rejection_reasons"]}
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ineligible to apply: {'; '.join(eval_result['rejection_reasons'])}"
            )

        # 7. Create Application
        application = Application(
            student_id=student_id,
            job_id=job_id,
            stage=ApplicationStage.APPLIED,
            applied_at=datetime.now(timezone.utc)
        )
        db.add(application)
        await db.flush()

        # 8. Record Status History
        history = ApplicationStatusHistory(
            application_id=application.id,
            from_stage="NONE",
            to_stage=ApplicationStage.APPLIED,
            changed_by_user_id=actor_user_id,
            reason="Application submitted by student.",
            changed_at=datetime.now(timezone.utc)
        )
        db.add(history)

        await db.commit()
        await db.refresh(application)
        return application

    @staticmethod
    async def transition_stage(
        db: AsyncSession,
        application_id: int,
        target_stage: ApplicationStage,
        actor_user_id: int,
        reason: Optional[str] = None
    ) -> Application:
        """
        Executes a strictly validated status transition with audit history.
        No backward or skipped transitions in standard progression.
        """
        app_query = (
            select(Application)
            .options(selectinload(Application.student))
            .where(Application.id == application_id)
        )
        res = await db.execute(app_query)
        application = res.scalar_one_or_none()
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        current_stage = application.stage
        allowed_targets = VALID_TRANSITIONS.get(current_stage, [])

        if target_stage not in allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stage transition from {current_stage} to {target_stage}. Allowed transitions: {allowed_targets}."
            )

        application.stage = target_stage
        application.updated_at = datetime.now(timezone.utc)

        history = ApplicationStatusHistory(
            application_id=application.id,
            from_stage=current_stage,
            to_stage=target_stage,
            changed_by_user_id=actor_user_id,
            reason=reason or f"Transitioned to {target_stage}",
            changed_at=datetime.now(timezone.utc)
        )
        db.add(history)

        # If shortlisting, enqueue notification
        if target_stage == ApplicationStage.SHORTLISTED and application.student:
            await OutboxService.queue_notification(
                db=db,
                user_id=application.student.user_id,
                template_name="APPLICATION_SHORTLISTED",
                payload={"application_id": application.id, "job_id": application.job_id}
            )

        await db.commit()
        await db.refresh(application)
        return application
