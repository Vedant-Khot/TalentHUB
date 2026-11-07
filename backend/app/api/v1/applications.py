from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_student, require_roles
from app.models.entities import (
    Application, Student, JobListing, User, InterviewSlot,
    Offer, ApplicationStatusHistory, Company
)
from app.models.enums import ApplicationStage, UserRole
from app.schemas.application import (
    ApplicationCreate, ApplicationResponse, InterviewSlotResponse,
    OfferResponse, ApplicationStatusHistoryResponse
)
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])

def build_app_response(app: Application) -> ApplicationResponse:
    interviews = [
        InterviewSlotResponse(
            id=slot.id,
            application_id=slot.application_id,
            round_number=slot.round_number,
            scheduled_time=slot.scheduled_time,
            venue_or_link=slot.venue_or_link,
            status=slot.status,
            result=slot.result,
            notes=slot.notes
        )
        for slot in app.interview_slots
    ]

    offer = None
    if app.offer:
        offer = OfferResponse(
            id=app.offer.id,
            application_id=app.offer.application_id,
            package_lpa=app.offer.package_lpa,
            issue_date=app.offer.issue_date,
            acceptance_deadline=app.offer.acceptance_deadline,
            letter_storage_key=app.offer.letter_storage_key,
            status=app.offer.status,
            response_timestamp=app.offer.response_timestamp
        )

    history = [
        ApplicationStatusHistoryResponse(
            id=h.id,
            from_stage=h.from_stage,
            to_stage=h.to_stage,
            changed_by_user_id=h.changed_by_user_id,
            reason=h.reason,
            changed_at=h.changed_at
        )
        for h in app.status_history
    ]

    return ApplicationResponse(
        id=app.id,
        student_id=app.student_id,
        student_name=app.student.full_name if app.student else "Unknown",
        student_usn=app.student.usn if app.student else "Unknown",
        student_branch=app.student.branch if app.student else "Unknown",
        student_cgpa=app.student.cgpa if app.student else 0.0,
        job_id=app.job_id,
        job_title=app.job.title if app.job else "Unknown",
        company_name=app.job.company.name if app.job and app.job.company else "Unknown",
        package_lpa=app.job.package_lpa if app.job else 0.0,
        stage=app.stage,
        applied_at=app.applied_at,
        interviews=interviews,
        offer=offer,
        history=history
    )

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def submit_application(
    data: ApplicationCreate,
    student: Student = Depends(get_current_student),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    app = await ApplicationService.apply_to_job(
        db=db,
        student_id=student.id,
        job_id=data.job_id,
        actor_user_id=current_user.id
    )

    query = (
        select(Application)
        .options(
            selectinload(Application.student),
            selectinload(Application.job).selectinload(JobListing.company),
            selectinload(Application.interview_slots),
            selectinload(Application.offer),
            selectinload(Application.status_history)
        )
        .where(Application.id == app.id)
    )
    res = await db.execute(query)
    full_app = res.scalar_one()
    return build_app_response(full_app)

@router.get("/my", response_model=List[ApplicationResponse])
async def get_my_applications(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Application)
        .options(
            selectinload(Application.student),
            selectinload(Application.job).selectinload(JobListing.company),
            selectinload(Application.interview_slots),
            selectinload(Application.offer),
            selectinload(Application.status_history)
        )
        .where(Application.student_id == student.id)
        .order_by(Application.applied_at.desc())
    )
    res = await db.execute(query)
    apps = res.scalars().all()
    return [build_app_response(a) for a in apps]

@router.get("/", response_model=List[ApplicationResponse])
async def list_coordinator_applicants(
    job_id: Optional[int] = None,
    stage: Optional[ApplicationStage] = None,
    branch: Optional[str] = None,
    search: Optional[str] = None,
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Application)
        .join(Student, Application.student_id == Student.id)
        .options(
            selectinload(Application.student),
            selectinload(Application.job).selectinload(JobListing.company),
            selectinload(Application.interview_slots),
            selectinload(Application.offer),
            selectinload(Application.status_history)
        )
    )

    if job_id:
        query = query.where(Application.job_id == job_id)
    if stage:
        query = query.where(Application.stage == stage)
    if branch:
        query = query.where(Student.branch == branch)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            (Student.full_name.ilike(search_pattern)) | (Student.usn.ilike(search_pattern))
        )

    query = query.order_by(Application.applied_at.desc())
    res = await db.execute(query)
    apps = res.scalars().all()
    return [build_app_response(a) for a in apps]

@router.post("/{application_id}/shortlist", response_model=ApplicationResponse)
async def shortlist_application(
    application_id: int,
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    app = await ApplicationService.transition_stage(
        db=db,
        application_id=application_id,
        target_stage=ApplicationStage.SHORTLISTED,
        actor_user_id=coordinator.id,
        reason="Shortlisted by placement coordinator for interview rounds."
    )

    query = (
        select(Application)
        .options(
            selectinload(Application.student),
            selectinload(Application.job).selectinload(JobListing.company),
            selectinload(Application.interview_slots),
            selectinload(Application.offer),
            selectinload(Application.status_history)
        )
        .where(Application.id == app.id)
    )
    res = await db.execute(query)
    return build_app_response(res.scalar_one())
