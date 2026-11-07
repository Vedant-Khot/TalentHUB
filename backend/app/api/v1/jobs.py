from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.db.session import get_db
from app.api.deps import get_current_user, require_roles
from app.models.entities import (
    JobListing, JobAllowedBranch, Company, PlacementSeason,
    Student, Application, User
)
from app.models.enums import JobStatus, UserRole, BranchName
from app.schemas.job import JobCreate, JobUpdate, JobResponse, EligibilityCheckResult
from app.services.eligibility_service import EligibilityService

router = APIRouter(prefix="/jobs", tags=["Job Drives"])

@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    eligible_only: bool = Query(False, description="Filter drives to only those the student is eligible for"),
    season_id: Optional[int] = None,
    status_filter: Optional[JobStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(JobListing)
        .options(
            selectinload(JobListing.company),
            selectinload(JobListing.season),
            selectinload(JobListing.allowed_branches)
        )
    )

    # Coordinators see all, students see PUBLISHED by default unless specified
    if current_user.role == UserRole.STUDENT:
        query = query.where(JobListing.status == JobStatus.PUBLISHED)
    elif status_filter:
        query = query.where(JobListing.status == status_filter)

    if season_id:
        query = query.where(JobListing.season_id == season_id)

    query = query.order_by(JobListing.drive_date.asc(), JobListing.id.desc())
    res = await db.execute(query)
    jobs = res.scalars().all()

    # If student, evaluate eligibility and application status for each job
    student: Optional[Student] = current_user.student if current_user.role == UserRole.STUDENT else None
    
    output = []
    for job in jobs:
        allowed_branch_names = [b.branch for b in job.allowed_branches]
        is_open_to_all = len(allowed_branch_names) == 0

        eligibility_result = None
        has_applied = False
        app_stage = None

        if student:
            # Check applied
            app_res = await db.execute(
                select(Application).where(Application.student_id == student.id, Application.job_id == job.id)
            )
            app = app_res.scalar_one_or_none()
            if app:
                has_applied = True
                app_stage = app.stage

            # Evaluate eligibility
            eval_dict = await EligibilityService.evaluate_eligibility(db, student, job)
            eligibility_result = EligibilityCheckResult(
                is_eligible=eval_dict["is_eligible"],
                cgpa_pass=eval_dict["cgpa_pass"],
                backlogs_pass=eval_dict["backlogs_pass"],
                season_offer_pass=eval_dict["season_offer_pass"],
                branch_pass=eval_dict["branch_pass"],
                rejection_reasons=eval_dict["rejection_reasons"],
                inputs_evaluated=eval_dict["inputs_evaluated"]
            )

            if eligible_only and not eligibility_result.is_eligible:
                continue

        output.append(JobResponse(
            id=job.id,
            company_id=job.company_id,
            company_name=job.company.name if job.company else "Unknown",
            season_id=job.season_id,
            season_name=job.season.name if job.season else "Unknown",
            title=job.title,
            description=job.description,
            min_cgpa=job.min_cgpa,
            max_backlogs=job.max_backlogs,
            package_lpa=job.package_lpa,
            drive_date=job.drive_date,
            deadline=job.deadline,
            status=job.status,
            allowed_branches=allowed_branch_names,
            is_open_to_all_branches=is_open_to_all,
            eligibility=eligibility_result,
            has_applied=has_applied,
            application_stage=app_stage
        ))

    return output

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_details(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(JobListing)
        .options(
            selectinload(JobListing.company),
            selectinload(JobListing.season),
            selectinload(JobListing.allowed_branches)
        )
        .where(JobListing.id == job_id)
    )
    res = await db.execute(query)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job drive not found.")

    allowed_branch_names = [b.branch for b in job.allowed_branches]
    is_open_to_all = len(allowed_branch_names) == 0

    student: Optional[Student] = current_user.student if current_user.role == UserRole.STUDENT else None
    eligibility_result = None
    has_applied = False
    app_stage = None

    if student:
        app_res = await db.execute(
            select(Application).where(Application.student_id == student.id, Application.job_id == job.id)
        )
        app = app_res.scalar_one_or_none()
        if app:
            has_applied = True
            app_stage = app.stage

        eval_dict = await EligibilityService.evaluate_eligibility(db, student, job)
        eligibility_result = EligibilityCheckResult(
            is_eligible=eval_dict["is_eligible"],
            cgpa_pass=eval_dict["cgpa_pass"],
            backlogs_pass=eval_dict["backlogs_pass"],
            season_offer_pass=eval_dict["season_offer_pass"],
            branch_pass=eval_dict["branch_pass"],
            rejection_reasons=eval_dict["rejection_reasons"],
            inputs_evaluated=eval_dict["inputs_evaluated"]
        )

    return JobResponse(
        id=job.id,
        company_id=job.company_id,
        company_name=job.company.name if job.company else "Unknown",
        season_id=job.season_id,
        season_name=job.season.name if job.season else "Unknown",
        title=job.title,
        description=job.description,
        min_cgpa=job.min_cgpa,
        max_backlogs=job.max_backlogs,
        package_lpa=job.package_lpa,
        drive_date=job.drive_date,
        deadline=job.deadline,
        status=job.status,
        allowed_branches=allowed_branch_names,
        is_open_to_all_branches=is_open_to_all,
        eligibility=eligibility_result,
        has_applied=has_applied,
        application_stage=app_stage
    )

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job_drive(
    data: JobCreate,
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    # Verify company and season exist
    company = await db.get(Company, data.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    season = await db.get(PlacementSeason, data.season_id)
    if not season:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement season not found.")

    job = JobListing(
        company_id=data.company_id,
        season_id=data.season_id,
        title=data.title.strip(),
        description=data.description.strip(),
        min_cgpa=data.min_cgpa,
        max_backlogs=data.max_backlogs,
        package_lpa=data.package_lpa,
        drive_date=data.drive_date,
        deadline=data.deadline,
        status=data.status
    )
    db.add(job)
    await db.flush()

    for branch_enum in data.allowed_branches:
        branch_rule = JobAllowedBranch(job_id=job.id, branch=branch_enum)
        db.add(branch_rule)

    await db.commit()
    await db.refresh(job)
    return await get_job_details(job_id=job.id, current_user=coordinator, db=db)

@router.put("/{job_id}/status", response_model=JobResponse)
async def update_job_status(
    job_id: int,
    new_status: JobStatus,
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    job = await db.get(JobListing, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job drive not found.")

    job.status = new_status
    await db.commit()
    return await get_job_details(job_id=job.id, current_user=coordinator, db=db)
