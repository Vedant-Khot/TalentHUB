import pytest
import pytest_asyncio
import os
from datetime import date, datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event

from app.db.base import Base
from app.models.entities import (
    User, Student, Company, PlacementSeason, JobListing,
    Application, InterviewSlot, Offer
)
from app.models.enums import (
    UserRole, BranchName, JobStatus, ApplicationStage,
    InterviewStatus, InterviewResult, OfferStatus
)
from app.services.interview_and_offer_service import InterviewService, OfferService
from app.core.config import settings

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
async def test_interview_scheduling_and_rescheduling(async_db: AsyncSession):
    company = Company(name="Netflix")
    season = PlacementSeason(year=2026, name="2026 Season", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    coord_user = User(email="coord_int@college.edu", password_hash="hash", role=UserRole.PLACEMENT_COORDINATOR)
    student_user = User(email="student_int@college.edu", password_hash="hash", role=UserRole.STUDENT)
    async_db.add_all([company, season, coord_user, student_user])
    await async_db.commit()

    student = Student(user_id=student_user.id, usn="1MS21CS301", full_name="Alice", email="student_int@college.edu", branch=BranchName.CSE, cgpa=8.8)
    job = JobListing(company_id=company.id, season_id=season.id, title="Backend Dev", description="Role", min_cgpa=7.0, drive_date=date(2026, 10, 20), deadline=date(2026, 10, 19), status=JobStatus.PUBLISHED)
    async_db.add_all([student, job])
    await async_db.commit()

    app = Application(student_id=student.id, job_id=job.id, stage=ApplicationStage.SHORTLISTED)
    async_db.add(app)
    await async_db.commit()

    # Schedule Round 1
    slot_time = datetime.now(timezone.utc) + timedelta(days=2)
    slot1 = await InterviewService.schedule_round(
        db=async_db,
        application_id=app.id,
        round_number=1,
        scheduled_time=slot_time,
        venue_or_link="Seminar Hall 1",
        actor_user_id=coord_user.id,
        notes="Technical Round 1"
    )
    assert slot1.round_number == 1
    assert slot1.status == InterviewStatus.SCHEDULED

    # Verify application stage became INTERVIEW_SCHEDULED
    await async_db.refresh(app)
    assert app.stage == ApplicationStage.INTERVIEW_SCHEDULED

    # Attempting to schedule duplicate Round 1 -> Must FAIL with 409
    with pytest.raises(HTTPException) as exc_info:
        await InterviewService.schedule_round(
            db=async_db,
            application_id=app.id,
            round_number=1,
            scheduled_time=slot_time,
            venue_or_link="Lab 2",
            actor_user_id=coord_user.id
        )
    assert exc_info.value.status_code == 409

    # Reschedule Round 1 safely
    new_time = slot_time + timedelta(hours=3)
    rescheduled_slot = await InterviewService.reschedule_round(
        db=async_db,
        slot_id=slot1.id,
        new_time=new_time,
        venue_or_link="Virtual Room A"
    )
    assert rescheduled_slot.status == InterviewStatus.RESCHEDULED
    assert rescheduled_slot.venue_or_link == "Virtual Room A"

    # Mark interview round as PASSED and conclude interviews
    completed_slot = await InterviewService.record_result(
        db=async_db,
        slot_id=slot1.id,
        result=InterviewResult.PASSED,
        actor_user_id=coord_user.id,
        mark_all_rounds_complete=True
    )
    assert completed_slot.result == InterviewResult.PASSED
    await async_db.refresh(app)
    assert app.stage == ApplicationStage.INTERVIEWED

@pytest.mark.asyncio
async def test_offer_issuance_and_season_acceptance(async_db: AsyncSession):
    company1 = Company(name="Oracle")
    company2 = Company(name="Cisco")
    season = PlacementSeason(year=2026, name="2026 Season", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    coord_user = User(email="coord_off@college.edu", password_hash="hash", role=UserRole.PLACEMENT_COORDINATOR)
    student1_user = User(email="s1_off@college.edu", password_hash="hash", role=UserRole.STUDENT)
    student2_user = User(email="s2_off@college.edu", password_hash="hash", role=UserRole.STUDENT)
    async_db.add_all([company1, company2, season, coord_user, student1_user, student2_user])
    await async_db.commit()

    student1 = Student(user_id=student1_user.id, usn="1MS21CS302", full_name="Bob", email="s1_off@college.edu", branch=BranchName.CSE, cgpa=8.5)
    job1 = JobListing(company_id=company1.id, season_id=season.id, title="Database Eng", description="Role", min_cgpa=7.0, drive_date=date(2026, 10, 20), deadline=date(2026, 10, 19), status=JobStatus.PUBLISHED)
    job2 = JobListing(company_id=company2.id, season_id=season.id, title="Network Eng", description="Role", min_cgpa=7.0, drive_date=date(2026, 10, 21), deadline=date(2026, 10, 19), status=JobStatus.PUBLISHED)
    async_db.add_all([student1, job1, job2])
    await async_db.commit()

    app1 = Application(student_id=student1.id, job_id=job1.id, stage=ApplicationStage.INTERVIEWED)
    app2 = Application(student_id=student1.id, job_id=job2.id, stage=ApplicationStage.INTERVIEWED)
    async_db.add_all([app1, app2])
    await async_db.commit()

    # Issue offer for App 1
    offer1 = await OfferService.create_offer(
        db=async_db,
        application_id=app1.id,
        package_lpa=16.5,
        actor_user_id=coord_user.id
    )
    assert offer1.package_lpa == 16.5
    assert offer1.status == OfferStatus.PENDING
    assert offer1.letter_storage_key is not None

    # Verify physical file created in storage
    expected_file = os.path.join(settings.OFFERS_STORAGE_DIR, f"{offer1.letter_storage_key}.pdf")
    assert os.path.exists(expected_file)

    # Issue offer for App 2
    offer2 = await OfferService.create_offer(
        db=async_db,
        application_id=app2.id,
        package_lpa=18.0,
        actor_user_id=coord_user.id
    )

    # Student 2 attempts to accept Student 1's offer -> Forbidden 403
    with pytest.raises(HTTPException) as exc_info:
        await OfferService.respond_to_offer(
            db=async_db,
            offer_id=offer1.id,
            student_user_id=student2_user.id,
            action="ACCEPT"
        )
    assert exc_info.value.status_code == 403

    # Student 1 accepts Offer 1 -> Succeeds
    accepted_offer1 = await OfferService.respond_to_offer(
        db=async_db,
        offer_id=offer1.id,
        student_user_id=student1_user.id,
        action="ACCEPT"
    )
    assert accepted_offer1.status == OfferStatus.ACCEPTED
    await async_db.refresh(app1)
    assert app1.stage == ApplicationStage.ACCEPTED

    # Now Student 1 attempts to ALSO accept Offer 2 in the same season -> Must FAIL with 409 Conflict
    with pytest.raises(HTTPException) as exc_info2:
        await OfferService.respond_to_offer(
            db=async_db,
            offer_id=offer2.id,
            student_user_id=student1_user.id,
            action="ACCEPT"
        )
    assert exc_info2.value.status_code == 409
    assert "already accepted an offer in this placement season" in str(exc_info2.value.detail)
