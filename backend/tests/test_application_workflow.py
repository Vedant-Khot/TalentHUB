import pytest
import pytest_asyncio
from datetime import date, datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event, select

from app.db.base import Base
from app.models.entities import (
    User, Student, Company, PlacementSeason, JobListing,
    Application, StudentConsent, ApplicationStatusHistory
)
from app.models.enums import UserRole, BranchName, JobStatus, ApplicationStage
from app.services.application_service import ApplicationService
from app.services.consent_service import ConsentService

@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_full_linear_application_workflow(async_db: AsyncSession):
    # Setup
    company = Company(name="Google")
    season = PlacementSeason(year=2026, name="2026 Season", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    coord_user = User(email="coord@college.edu", password_hash="hash", role=UserRole.PLACEMENT_COORDINATOR)
    student_user = User(email="applicant@college.edu", password_hash="hash", role=UserRole.STUDENT)
    async_db.add_all([company, season, coord_user, student_user])
    await async_db.commit()

    student = Student(
        user_id=student_user.id, usn="1MS21CS201", full_name="John Doe", email="applicant@college.edu",
        branch=BranchName.CSE, cgpa=9.2, active_backlogs=0, cleared_backlogs=0
    )
    job = JobListing(
        company_id=company.id, season_id=season.id, title="Software Engineer", description="Role",
        min_cgpa=8.0, max_backlogs=0, package_lpa=24.0, drive_date=date(2026, 10, 25), deadline=date(2026, 10, 24),
        status=JobStatus.PUBLISHED
    )
    async_db.add_all([student, job])
    await async_db.commit()

    # Attempt to apply WITHOUT consent -> Must FAIL
    with pytest.raises(HTTPException) as exc_info:
        await ApplicationService.apply_to_job(async_db, student.id, job.id, student_user.id)
    assert exc_info.value.status_code == 403

    # Grant consent
    await ConsentService.record_consent(async_db, student.id, is_granted=True)

    # Now apply -> Must succeed with stage APPLIED
    app = await ApplicationService.apply_to_job(async_db, student.id, job.id, student_user.id)
    assert app.stage == ApplicationStage.APPLIED

    # Check status history recorded
    hist_res = await async_db.execute(select(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id == app.id))
    histories = hist_res.scalars().all()
    assert len(histories) == 1
    assert histories[0].to_stage == ApplicationStage.APPLIED

    # 1. Transition APPLIED -> SHORTLISTED
    app = await ApplicationService.transition_stage(
        async_db, app.id, ApplicationStage.SHORTLISTED, coord_user.id, reason="Profile shortlisted"
    )
    assert app.stage == ApplicationStage.SHORTLISTED

    # 2. Transition SHORTLISTED -> INTERVIEW_SCHEDULED
    app = await ApplicationService.transition_stage(
        async_db, app.id, ApplicationStage.INTERVIEW_SCHEDULED, coord_user.id, reason="Round 1 scheduled"
    )
    assert app.stage == ApplicationStage.INTERVIEW_SCHEDULED

    # 3. Transition INTERVIEW_SCHEDULED -> INTERVIEWED
    app = await ApplicationService.transition_stage(
        async_db, app.id, ApplicationStage.INTERVIEWED, coord_user.id, reason="All interview rounds completed"
    )
    assert app.stage == ApplicationStage.INTERVIEWED

    # 4. Transition INTERVIEWED -> OFFERED
    app = await ApplicationService.transition_stage(
        async_db, app.id, ApplicationStage.OFFERED, coord_user.id, reason="Offer released"
    )
    assert app.stage == ApplicationStage.OFFERED

    # 5. Transition OFFERED -> ACCEPTED
    app = await ApplicationService.transition_stage(
        async_db, app.id, ApplicationStage.ACCEPTED, student_user.id, reason="Offer accepted by student"
    )
    assert app.stage == ApplicationStage.ACCEPTED

    # Verify total history entries
    hist_res2 = await async_db.execute(select(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id == app.id))
    all_histories = hist_res2.scalars().all()
    assert len(all_histories) == 6

@pytest.mark.asyncio
async def test_invalid_and_backward_transitions_rejected(async_db: AsyncSession):
    company = Company(name="Meta")
    season = PlacementSeason(year=2026, name="2026 Season", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    coord_user = User(email="coord2@college.edu", password_hash="hash", role=UserRole.PLACEMENT_COORDINATOR)
    student_user = User(email="student2@college.edu", password_hash="hash", role=UserRole.STUDENT)
    async_db.add_all([company, season, coord_user, student_user])
    await async_db.commit()

    student = Student(
        user_id=student_user.id, usn="1MS21CS202", full_name="Jane Doe", email="student2@college.edu",
        branch=BranchName.CSE, cgpa=8.5, active_backlogs=0, cleared_backlogs=0
    )
    job = JobListing(
        company_id=company.id, season_id=season.id, title="Frontend Engineer", description="Role",
        min_cgpa=7.0, max_backlogs=0, package_lpa=18.0, drive_date=date(2026, 10, 25), deadline=date(2026, 10, 24),
        status=JobStatus.PUBLISHED
    )
    async_db.add_all([student, job])
    await async_db.commit()

    await ConsentService.record_consent(async_db, student.id, is_granted=True)
    app = await ApplicationService.apply_to_job(async_db, student.id, job.id, student_user.id)

    # Attempting to jump directly from APPLIED to OFFERED -> Must FAIL
    with pytest.raises(HTTPException) as exc_info:
        await ApplicationService.transition_stage(async_db, app.id, ApplicationStage.OFFERED, coord_user.id)
    assert exc_info.value.status_code == 400

    # Shortlist application
    await ApplicationService.transition_stage(async_db, app.id, ApplicationStage.SHORTLISTED, coord_user.id)

    # Attempt backward transition from SHORTLISTED back to APPLIED -> Must FAIL
    with pytest.raises(HTTPException) as exc_info2:
        await ApplicationService.transition_stage(async_db, app.id, ApplicationStage.APPLIED, coord_user.id)
    assert exc_info2.value.status_code == 400

@pytest.mark.asyncio
async def test_same_company_same_season_lockout(async_db: AsyncSession):
    company = Company(name="Apple")
    season = PlacementSeason(year=2026, name="2026 Season", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    student_user = User(email="appleapp@college.edu", password_hash="hash", role=UserRole.STUDENT)
    async_db.add_all([company, season, student_user])
    await async_db.commit()

    student = Student(
        user_id=student_user.id, usn="1MS21CS203", full_name="Tim", email="appleapp@college.edu",
        branch=BranchName.CSE, cgpa=9.5, active_backlogs=0, cleared_backlogs=0
    )
    # Role 1 at Apple
    job1 = JobListing(
        company_id=company.id, season_id=season.id, title="iOS Developer", description="Role 1",
        min_cgpa=8.0, max_backlogs=0, package_lpa=30.0, drive_date=date(2026, 10, 25), deadline=date(2026, 10, 24),
        status=JobStatus.PUBLISHED
    )
    # Role 2 at Apple (different role, same company, same season)
    job2 = JobListing(
        company_id=company.id, season_id=season.id, title="macOS Core Engineer", description="Role 2",
        min_cgpa=8.0, max_backlogs=0, package_lpa=35.0, drive_date=date(2026, 10, 26), deadline=date(2026, 10, 24),
        status=JobStatus.PUBLISHED
    )
    async_db.add_all([student, job1, job2])
    await async_db.commit()

    await ConsentService.record_consent(async_db, student.id, is_granted=True)

    # Student applies to Role 1 -> Succeeds
    await ApplicationService.apply_to_job(async_db, student.id, job1.id, student_user.id)

    # Student attempts to apply to Role 2 (same company, same season) -> Must FAIL with 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        await ApplicationService.apply_to_job(async_db, student.id, job2.id, student_user.id)
    assert exc_info.value.status_code == 409
    assert "already applied to this company in this placement season" in str(exc_info.value.detail)
