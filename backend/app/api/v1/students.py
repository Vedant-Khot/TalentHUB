from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.db.session import get_db
from app.api.deps import get_current_student, get_current_user
from app.models.entities import (
    Student, User, PlacementSeason, Application, InterviewSlot,
    JobListing, Offer
)
from app.models.enums import ApplicationStage, JobStatus, InterviewStatus, OfferStatus
from app.schemas.student import StudentResponse, StudentUpdate
from app.schemas.auth import ConsentRequest, ConsentResponse
from app.services.consent_service import ConsentService
from app.services.eligibility_service import EligibilityService

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/me", response_model=StudentResponse)
async def get_my_profile(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    has_consent = await ConsentService.has_active_consent(db, student.id)
    # Check if student accepted an offer in current active season
    active_season_res = await db.execute(
        select(PlacementSeason).where(PlacementSeason.is_active == True).limit(1)
    )
    active_season = active_season_res.scalar_one_or_none()
    accepted_offer = False
    if active_season:
        accepted_offer = await EligibilityService.has_accepted_offer_in_season(
            db, student.id, active_season.id
        )

    return StudentResponse(
        id=student.id,
        user_id=student.user_id,
        usn=student.usn,
        full_name=student.full_name,
        email=student.email,
        branch=student.branch,
        cgpa=student.cgpa,
        active_backlogs=student.active_backlogs,
        cleared_backlogs=student.cleared_backlogs,
        phone=student.phone,
        has_active_consent=has_consent,
        accepted_offer_this_season=accepted_offer
    )

@router.put("/me", response_model=StudentResponse)
async def update_my_profile(
    update_data: StudentUpdate,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    if update_data.full_name is not None:
        student.full_name = update_data.full_name
    if update_data.phone is not None:
        student.phone = update_data.phone
    if update_data.cgpa is not None:
        student.cgpa = update_data.cgpa
    if update_data.active_backlogs is not None:
        student.active_backlogs = update_data.active_backlogs
    if update_data.cleared_backlogs is not None:
        student.cleared_backlogs = update_data.cleared_backlogs

    await db.commit()
    await db.refresh(student)
    return await get_my_profile(student=student, db=db)

@router.post("/me/consent", response_model=ConsentResponse)
async def manage_consent(
    consent_data: ConsentRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    consent = await ConsentService.record_consent(
        db=db,
        student_id=student.id,
        policy_version=consent_data.policy_version,
        purpose=consent_data.purpose,
        is_granted=consent_data.is_granted
    )
    return ConsentResponse(
        id=consent.id,
        student_id=consent.student_id,
        policy_version=consent.policy_version,
        purpose=consent.purpose,
        is_granted=consent.is_granted,
        event_timestamp=consent.event_timestamp.isoformat()
    )

@router.get("/dashboard")
async def get_student_dashboard(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # Active season
    season_res = await db.execute(
        select(PlacementSeason).where(PlacementSeason.is_active == True).limit(1)
    )
    active_season = season_res.scalar_one_or_none()

    # Stage counts
    stage_counts = {
        ApplicationStage.APPLIED.value: 0,
        ApplicationStage.SHORTLISTED.value: 0,
        ApplicationStage.INTERVIEW_SCHEDULED.value: 0,
        ApplicationStage.INTERVIEWED.value: 0,
        ApplicationStage.OFFERED.value: 0,
        ApplicationStage.ACCEPTED.value: 0,
    }
    apps_res = await db.execute(
        select(Application.stage, func.count(Application.id))
        .where(Application.student_id == student.id)
        .group_by(Application.stage)
    )
    for stage, count in apps_res.all():
        if stage in stage_counts:
            stage_counts[stage] = count

    # Upcoming interview
    now_utc = datetime.now(timezone.utc)
    interview_res = await db.execute(
        select(InterviewSlot)
        .join(Application, InterviewSlot.application_id == Application.id)
        .join(JobListing, Application.job_id == JobListing.id)
        .options(
            selectinload(InterviewSlot.application).selectinload(Application.job).selectinload(JobListing.company)
        )
        .where(
            Application.student_id == student.id,
            InterviewSlot.status == InterviewStatus.SCHEDULED,
            InterviewSlot.scheduled_time >= now_utc
        )
        .order_by(InterviewSlot.scheduled_time.asc())
        .limit(1)
    )
    upcoming_slot = interview_res.scalar_one_or_none()
    upcoming_interview = None
    if upcoming_slot:
        job = upcoming_slot.application.job
        upcoming_interview = {
            "slot_id": upcoming_slot.id,
            "company_name": job.company.name if job and job.company else "Unknown",
            "job_title": job.title if job else "",
            "round_number": upcoming_slot.round_number,
            "scheduled_time": upcoming_slot.scheduled_time.isoformat(),
            "venue_or_link": upcoming_slot.venue_or_link,
            "notes": upcoming_slot.notes
        }

    # Open & eligible drives preview (limit 5)
    open_jobs_query = (
        select(JobListing)
        .options(selectinload(JobListing.company), selectinload(JobListing.allowed_branches))
        .where(JobListing.status == JobStatus.PUBLISHED)
        .order_by(JobListing.drive_date.asc())
        .limit(10)
    )
    jobs_res = await db.execute(open_jobs_query)
    open_jobs = jobs_res.scalars().all()

    eligible_drives = []
    has_accepted_season_offer = False
    if active_season:
        has_accepted_season_offer = await EligibilityService.has_accepted_offer_in_season(
            db, student.id, active_season.id
        )

    for job in open_jobs:
        eligibility = await EligibilityService.evaluate_eligibility(db, student, job)
        if eligibility["is_eligible"]:
            # Check if student applied
            app_check = await db.execute(
                select(Application.id).where(Application.student_id == student.id, Application.job_id == job.id)
            )
            applied = app_check.scalar_one_or_none() is not None
            eligible_drives.append({
                "id": job.id,
                "title": job.title,
                "company_name": job.company.name if job.company else "",
                "package_lpa": job.package_lpa,
                "drive_date": job.drive_date.isoformat(),
                "deadline": job.deadline.isoformat(),
                "min_cgpa": job.min_cgpa,
                "has_applied": applied
            })

    return {
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "usn": student.usn,
            "branch": student.branch,
            "cgpa": student.cgpa,
            "active_backlogs": student.active_backlogs,
            "accepted_offer_this_season": has_accepted_season_offer
        },
        "active_season": {
            "id": active_season.id,
            "name": active_season.name,
            "year": active_season.year
        } if active_season else None,
        "stage_counts": stage_counts,
        "upcoming_interview": upcoming_interview,
        "eligible_drives": eligible_drives[:5]
    }
