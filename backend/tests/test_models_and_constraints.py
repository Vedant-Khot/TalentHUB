import pytest
from datetime import date, datetime, timezone
from sqlalchemy.exc import IntegrityError
from app.models.entities import (
    User, Student, Company, PlacementSeason, JobListing,
    JobAllowedBranch, Application, InterviewSlot, Offer
)
from app.models.enums import UserRole, BranchName, JobStatus, ApplicationStage, InterviewStatus, InterviewResult, OfferStatus

def test_valid_student_creation(db_session):
    user = User(email="teststudent@college.edu", password_hash="hash", role=UserRole.STUDENT)
    db_session.add(user)
    db_session.commit()

    student = Student(
        user_id=user.id,
        usn="1MS21CS001",
        full_name="Alice Smith",
        email="teststudent@college.edu",
        branch=BranchName.CSE,
        cgpa=8.75,
        active_backlogs=0,
        cleared_backlogs=0
    )
    db_session.add(student)
    db_session.commit()
    assert student.id is not None
    assert student.cgpa == 8.75

def test_cgpa_range_constraint(db_session):
    user = User(email="badcgpa@college.edu", password_hash="hash", role=UserRole.STUDENT)
    db_session.add(user)
    db_session.commit()

    # CGPA > 10.0 should fail
    bad_student = Student(
        user_id=user.id,
        usn="1MS21CS002",
        full_name="Bob",
        email="badcgpa@college.edu",
        branch=BranchName.CSE,
        cgpa=10.5,
        active_backlogs=0,
        cleared_backlogs=0
    )
    db_session.add(bad_student)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_negative_backlog_constraint(db_session):
    user = User(email="badbacklog@college.edu", password_hash="hash", role=UserRole.STUDENT)
    db_session.add(user)
    db_session.commit()

    bad_student = Student(
        user_id=user.id,
        usn="1MS21CS003",
        full_name="Charlie",
        email="badbacklog@college.edu",
        branch=BranchName.ECE,
        cgpa=7.5,
        active_backlogs=-1,
        cleared_backlogs=0
    )
    db_session.add(bad_student)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_unique_usn_constraint(db_session):
    user1 = User(email="u1@college.edu", password_hash="hash", role=UserRole.STUDENT)
    user2 = User(email="u2@college.edu", password_hash="hash", role=UserRole.STUDENT)
    db_session.add_all([user1, user2])
    db_session.commit()

    s1 = Student(user_id=user1.id, usn="1MS21CS010", full_name="User 1", email="u1@college.edu", branch=BranchName.ISE, cgpa=8.0)
    db_session.add(s1)
    db_session.commit()

    # Same USN should fail
    s2 = Student(user_id=user2.id, usn="1MS21CS010", full_name="User 2", email="u2@college.edu", branch=BranchName.ISE, cgpa=8.5)
    db_session.add(s2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_unique_application_per_student_and_job(db_session):
    user = User(email="app@college.edu", password_hash="hash", role=UserRole.STUDENT)
    company = Company(name="Google")
    season = PlacementSeason(year=2026, name="2026 Season", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    db_session.add_all([user, company, season])
    db_session.commit()

    student = Student(user_id=user.id, usn="1MS21CS020", full_name="Applicant", email="app@college.edu", branch=BranchName.CSE, cgpa=9.0)
    job = JobListing(
        company_id=company.id, season_id=season.id, title="SWE", description="Desc",
        min_cgpa=7.0, max_backlogs=0, package_lpa=25.0, drive_date=date(2026, 10, 15), deadline=date(2026, 10, 14),
        status=JobStatus.PUBLISHED
    )
    db_session.add_all([student, job])
    db_session.commit()

    app1 = Application(student_id=student.id, job_id=job.id, stage=ApplicationStage.APPLIED)
    db_session.add(app1)
    db_session.commit()

    # Duplicate application for the same job should fail
    app2 = Application(student_id=student.id, job_id=job.id, stage=ApplicationStage.APPLIED)
    db_session.add(app2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_unique_interview_round_per_application(db_session):
    user = User(email="round@college.edu", password_hash="hash", role=UserRole.STUDENT)
    company = Company(name="Microsoft")
    season = PlacementSeason(year=2026, name="2026 Season", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    db_session.add_all([user, company, season])
    db_session.commit()

    student = Student(user_id=user.id, usn="1MS21CS030", full_name="Applicant 2", email="round@college.edu", branch=BranchName.CSE, cgpa=9.0)
    job = JobListing(
        company_id=company.id, season_id=season.id, title="SDE-1", description="Desc",
        min_cgpa=7.0, max_backlogs=0, package_lpa=20.0, drive_date=date(2026, 10, 15), deadline=date(2026, 10, 14),
        status=JobStatus.PUBLISHED
    )
    db_session.add_all([student, job])
    db_session.commit()

    app = Application(student_id=student.id, job_id=job.id, stage=ApplicationStage.SHORTLISTED)
    db_session.add(app)
    db_session.commit()

    slot1 = InterviewSlot(application_id=app.id, round_number=1, scheduled_time=datetime.now(timezone.utc), venue_or_link="Lab 1")
    db_session.add(slot1)
    db_session.commit()

    # Duplicate round 1 should fail
    slot2 = InterviewSlot(application_id=app.id, round_number=1, scheduled_time=datetime.now(timezone.utc), venue_or_link="Lab 2")
    db_session.add(slot2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
