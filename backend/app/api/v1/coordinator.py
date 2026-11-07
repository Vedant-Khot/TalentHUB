from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.api.deps import require_roles
from app.models.entities import (
    User, Company, PlacementSeason, Student, JobListing,
    Application, Offer, NotificationLog
)
from app.models.enums import UserRole, OfferStatus, ApplicationStage
from app.schemas.job import (
    CompanyCreate, CompanyResponse, PlacementSeasonCreate, PlacementSeasonResponse
)
from app.services.outbox_service import OutboxService

router = APIRouter(prefix="/coordinator", tags=["Placement Coordinator"])

# Companies
@router.get("/companies", response_model=List[CompanyResponse])
async def list_companies(
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Company).order_by(Company.name.asc()))
    return res.scalars().all()

@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(select(Company).where(Company.name == data.name.strip()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company with this name already exists.")

    company = Company(
        name=data.name.strip(),
        website=data.website,
        contact_email=data.contact_email,
        description=data.description
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company

# Placement Seasons
@router.get("/seasons", response_model=List[PlacementSeasonResponse])
async def list_seasons(
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(PlacementSeason).order_by(PlacementSeason.year.desc()))
    return res.scalars().all()

@router.post("/seasons", response_model=PlacementSeasonResponse, status_code=status.HTTP_201_CREATED)
async def create_season(
    data: PlacementSeasonCreate,
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    season = PlacementSeason(
        year=data.year,
        name=data.name.strip(),
        is_active=data.is_active,
        start_date=data.start_date,
        end_date=data.end_date
    )
    db.add(season)
    await db.commit()
    await db.refresh(season)
    return season

# Analytics & Placement KPI Summary
@router.get("/analytics")
async def get_placement_analytics(
    season_id: Optional[int] = None,
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    # Total registered students
    total_students_res = await db.execute(select(func.count(Student.id)))
    total_students = total_students_res.scalar() or 0

    # Total drives
    total_drives_res = await db.execute(select(func.count(JobListing.id)))
    total_drives = total_drives_res.scalar() or 0

    # Placed students (unique students who accepted an offer)
    placed_query = (
        select(func.count(func.distinct(Application.student_id)))
        .join(Offer, Offer.application_id == Application.id)
        .where(Offer.status == OfferStatus.ACCEPTED)
    )
    if season_id:
        placed_query = placed_query.join(JobListing, Application.job_id == JobListing.id).where(JobListing.season_id == season_id)
    placed_students_res = await db.execute(placed_query)
    placed_students = placed_students_res.scalar() or 0

    # Package stats
    pkg_query = select(func.avg(Offer.package_lpa), func.max(Offer.package_lpa)).where(Offer.status == OfferStatus.ACCEPTED)
    if season_id:
        pkg_query = pkg_query.join(Application, Offer.application_id == Application.id).join(JobListing, Application.job_id == JobListing.id).where(JobListing.season_id == season_id)
    pkg_res = await db.execute(pkg_query)
    avg_lpa, max_lpa = pkg_res.one()

    # Stage distribution
    stages_res = await db.execute(
        select(Application.stage, func.count(Application.id)).group_by(Application.stage)
    )
    stage_breakdown = {stage: count for stage, count in stages_res.all()}

    # Branch-wise placement
    branch_placed_query = (
        select(Student.branch, func.count(func.distinct(Student.id)))
        .join(Application, Student.id == Application.student_id)
        .join(Offer, Offer.application_id == Application.id)
        .where(Offer.status == OfferStatus.ACCEPTED)
        .group_by(Student.branch)
    )
    branch_res = await db.execute(branch_placed_query)
    branch_placement = {b: count for b, count in branch_res.all()}

    return {
        "total_students": total_students,
        "total_drives": total_drives,
        "placed_students": placed_students,
        "placement_percentage": round((placed_students / total_students * 100), 1) if total_students > 0 else 0.0,
        "average_package_lpa": round(avg_lpa, 2) if avg_lpa else 0.0,
        "highest_package_lpa": round(max_lpa, 2) if max_lpa else 0.0,
        "stage_breakdown": stage_breakdown,
        "branch_placement": branch_placement
    }

# Process Outbox Notifications
@router.post("/process-outbox")
async def trigger_outbox_processing(
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    processed = await OutboxService.process_pending_notifications(db)
    return {"status": "success", "processed_count": len(processed)}
