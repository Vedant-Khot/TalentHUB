import pytest
import pytest_asyncio
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event

from app.db.base import Base
from app.models.entities import (
    User, Student, Company, PlacementSeason, JobListing,
    JobAllowedBranch, Application, Offer
)
from app.models.enums import (
    UserRole, BranchName, JobStatus, ApplicationStage, OfferStatus
)
from app.services.eligibility_service import EligibilityService

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
async def test_exact_cgpa_boundary(async_db: AsyncSession):
    # Setup company, season, job
    company = Company(name="TechCorp")
    season = PlacementSeason(year=2026, name="2026 Drive", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    async_db.add_all([company, season])
    await async_db.commit()

    job = JobListing(
        company_id=company.id, season_id=season.id, title="Software Engineer", description="Role",
        min_cgpa=7.50, max_backlogs=0, package_lpa=12.0, drive_date=date(2026, 10, 20), deadline=date(2026, 10, 19),
        status=JobStatus.PUBLISHED
    )
    async_db.add(job)
    await async_db.commit()

    # Student 1: Exact match 7.50 -> Must PASS
    user1 = User(email="exact@college.edu", password_hash="hash", role=UserRole.STUDENT)
    async_db.add(user1)
    await async_db.commit()
    s1 = Student(user_id=user1.id, usn="1MS21CS101", full_name="Student Exact", email="exact@college.edu", branch=BranchName.CSE, cgpa=7.50, active_backlogs=0, cleared_backlogs=0)
    async_db.add(s1)
    await async_db.commit()

    res1 = await EligibilityService.evaluate_eligibility(async_db, s1, job)
    assert res1["is_eligible"] is True
    assert res1["cgpa_pass"] is True

    # Student 2: 7.49 -> Must FAIL
    user2 = User(email="below@college.edu", password_hash="hash", role=UserRole.STUDENT)
    async_db.add(user2)
    await async_db.commit()
    s2 = Student(user_id=user2.id, usn="1MS21CS102", full_name="Student Below", email="below@college.edu", branch=BranchName.CSE, cgpa=7.49, active_backlogs=0, cleared_backlogs=0)
    async_db.add(s2)
    await async_db.commit()

    res2 = await EligibilityService.evaluate_eligibility(async_db, s2, job)
    assert res2["is_eligible"] is False
    assert res2["cgpa_pass"] is False
    assert any("below minimum required" in r for r in res2["rejection_reasons"])

@pytest.mark.asyncio
async def test_cleared_backlogs_do_not_affect_eligibility(async_db: AsyncSession):
    company = Company(name="FinTech")
    season = PlacementSeason(year=2026, name="2026 Drive", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    async_db.add_all([company, season])
    await async_db.commit()

    job = JobListing(
        company_id=company.id, season_id=season.id, title="Analyst", description="Role",
        min_cgpa=6.0, max_backlogs=0, package_lpa=10.0, drive_date=date(2026, 10, 20), deadline=date(2026, 10, 19),
        status=JobStatus.PUBLISHED
    )
    async_db.add(job)
    await async_db.commit()

    user = User(email="cleared@college.edu", password_hash="hash", role=UserRole.STUDENT)
    async_db.add(user)
    await async_db.commit()

    # Active backlogs: 0, Cleared backlogs: 3 -> Must PASS because max_backlogs is 0 active backlogs
    student = Student(
        user_id=user.id, usn="1MS21CS103", full_name="Student Cleared", email="cleared@college.edu",
        branch=BranchName.CSE, cgpa=8.0, active_backlogs=0, cleared_backlogs=3
    )
    async_db.add(student)
    await async_db.commit()

    res = await EligibilityService.evaluate_eligibility(async_db, student, job)
    assert res["is_eligible"] is True
    assert res["backlogs_pass"] is True

@pytest.mark.asyncio
async def test_empty_allowed_branches_is_open_to_all(async_db: AsyncSession):
    company = Company(name="OpenCorp")
    season = PlacementSeason(year=2026, name="2026 Drive", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    async_db.add_all([company, season])
    await async_db.commit()

    # Job with no job_allowed_branches rows -> Open to all branches
    job = JobListing(
        company_id=company.id, season_id=season.id, title="Consultant", description="Role",
        min_cgpa=6.0, max_backlogs=2, package_lpa=8.0, drive_date=date(2026, 10, 20), deadline=date(2026, 10, 19),
        status=JobStatus.PUBLISHED
    )
    async_db.add(job)
    await async_db.commit()

    # Check student from MECH
    user = User(email="mech@college.edu", password_hash="hash", role=UserRole.STUDENT)
    async_db.add(user)
    await async_db.commit()
    student = Student(
        user_id=user.id, usn="1MS21ME001", full_name="Student Mech", email="mech@college.edu",
        branch=BranchName.MECH, cgpa=7.0, active_backlogs=0, cleared_backlogs=0
    )
    async_db.add(student)
    await async_db.commit()

    res = await EligibilityService.evaluate_eligibility(async_db, student, job)
    assert res["is_eligible"] is True
    assert res["branch_pass"] is True

    # Now add restricted branch (CSE only)
    branch_rule = JobAllowedBranch(job_id=job.id, branch=BranchName.CSE)
    async_db.add(branch_rule)
    await async_db.commit()

    # Re-evaluate MECH student -> Must FAIL branch check
    res2 = await EligibilityService.evaluate_eligibility(async_db, student, job)
    assert res2["is_eligible"] is False
    assert res2["branch_pass"] is False
    assert any("Branch MECH is not eligible" in r for r in res2["rejection_reasons"])

@pytest.mark.asyncio
async def test_season_aware_accepted_offer_rule(async_db: AsyncSession):
    company1 = Company(name="Amazon")
    company2 = Company(name="Google")
    season2025 = PlacementSeason(year=2025, name="2025 Drive", start_date=date(2025, 1, 1), end_date=date(2025, 12, 31), is_active=False)
    season2026 = PlacementSeason(year=2026, name="2026 Drive", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), is_active=True)
    async_db.add_all([company1, company2, season2025, season2026])
    await async_db.commit()

    user = User(email="seasonoffer@college.edu", password_hash="hash", role=UserRole.STUDENT)
    async_db.add(user)
    await async_db.commit()
    student = Student(
        user_id=user.id, usn="1MS21CS105", full_name="Student MultiSeason", email="seasonoffer@college.edu",
        branch=BranchName.CSE, cgpa=9.0, active_backlogs=0, cleared_backlogs=0
    )
    async_db.add(student)
    await async_db.commit()

    # Job in season 2025 where student accepted offer
    job_2025 = JobListing(
        company_id=company1.id, season_id=season2025.id, title="Intern", description="Role",
        min_cgpa=6.0, max_backlogs=0, package_lpa=10.0, drive_date=date(2025, 10, 20), deadline=date(2025, 10, 19),
        status=JobStatus.CLOSED
    )
    async_db.add(job_2025)
    await async_db.commit()

    app_2025 = Application(student_id=student.id, job_id=job_2025.id, stage=ApplicationStage.ACCEPTED)
    async_db.add(app_2025)
    await async_db.commit()

    offer_2025 = Offer(
        application_id=app_2025.id, package_lpa=10.0, letter_storage_key="key_2025",
        status=OfferStatus.ACCEPTED
    )
    async_db.add(offer_2025)
    await async_db.commit()

    # Now Job in season 2026 -> Student MUST BE ELIGIBLE! A previous season's accepted offer must not block 2026 season.
    job_2026 = JobListing(
        company_id=company2.id, season_id=season2026.id, title="FTE", description="Role",
        min_cgpa=6.0, max_backlogs=0, package_lpa=25.0, drive_date=date(2026, 10, 20), deadline=date(2026, 10, 19),
        status=JobStatus.PUBLISHED
    )
    async_db.add(job_2026)
    await async_db.commit()

    res_2026 = await EligibilityService.evaluate_eligibility(async_db, student, job_2026)
    assert res_2026["is_eligible"] is True
    assert res_2026["season_offer_pass"] is True

    # If student accepts an offer in season 2026, they are now blocked for any OTHER job in season 2026
    app_2026 = Application(student_id=student.id, job_id=job_2026.id, stage=ApplicationStage.ACCEPTED)
    async_db.add(app_2026)
    await async_db.commit()

    offer_2026 = Offer(
        application_id=app_2026.id, package_lpa=25.0, letter_storage_key="key_2026",
        status=OfferStatus.ACCEPTED
    )
    async_db.add(offer_2026)
    await async_db.commit()

    # Another job in 2026 season
    job_2026_other = JobListing(
        company_id=company1.id, season_id=season2026.id, title="Architect", description="Role",
        min_cgpa=6.0, max_backlogs=0, package_lpa=30.0, drive_date=date(2026, 11, 20), deadline=date(2026, 11, 19),
        status=JobStatus.PUBLISHED
    )
    async_db.add(job_2026_other)
    await async_db.commit()

    res_2026_blocked = await EligibilityService.evaluate_eligibility(async_db, student, job_2026_other)
    assert res_2026_blocked["is_eligible"] is False
    assert res_2026_blocked["season_offer_pass"] is False
    assert any("already accepted an offer in this placement season" in r for r in res_2026_blocked["rejection_reasons"])
