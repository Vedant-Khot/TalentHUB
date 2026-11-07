import asyncio
import os
import sys
from datetime import date, datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.base import Base
from app.db.session import async_engine, AsyncSessionLocal
from app.models.entities import (
    User, Student, Company, PlacementSeason, JobListing,
    JobAllowedBranch, StudentConsent, Application, InterviewSlot,
    Offer, ApplicationStatusHistory
)
from app.models.enums import (
    UserRole, BranchName, JobStatus, ApplicationStage,
    InterviewStatus, InterviewResult, OfferStatus
)
from app.core.security import get_password_hash
from app.core.config import settings

async def seed():
    print("Seeding TalentHub database...")
    async with AsyncSessionLocal() as session:
        # 1. Placement Seasons
        season = PlacementSeason(
            year=2026,
            name="2026-2027 Campus Placement Drive",
            is_active=True,
            start_date=date(2026, 8, 1),
            end_date=date(2027, 6, 30)
        )
        session.add(season)
        await session.flush()

        # 2. Users & Coordinator
        coord_user = User(
            email="coordinator@college.edu",
            password_hash=get_password_hash("CoordinatorPass123!"),
            role=UserRole.PLACEMENT_COORDINATOR,
            is_active=True
        )
        session.add(coord_user)

        # 3. Companies
        c_google = Company(name="Google", website="https://careers.google.com", contact_email="campus@google.com", description="Global tech leader in search, cloud, and AI.")
        c_msft = Company(name="Microsoft", website="https://careers.microsoft.com", contact_email="university@microsoft.com", description="Empowering every person and organization.")
        c_amazon = Company(name="Amazon", website="https://amazon.jobs", contact_email="campus@amazon.com", description="Earth's most customer-centric company.")
        c_cisco = Company(name="Cisco Systems", website="https://cisco.com", contact_email="recruiting@cisco.com", description="Worldwide leader in networking and cybersecurity.")
        session.add_all([c_google, c_msft, c_amazon, c_cisco])
        await session.flush()

        # 4. Job Drives
        job_swe = JobListing(
            company_id=c_google.id,
            season_id=season.id,
            title="Software Engineer - University Graduate",
            description="Build large-scale distributed systems, web services, and machine learning infrastructure.",
            min_cgpa=8.0,
            max_backlogs=0,
            package_lpa=32.5,
            drive_date=date(2026, 10, 20),
            deadline=date(2026, 10, 18),
            status=JobStatus.PUBLISHED
        )
        job_cloud = JobListing(
            company_id=c_msft.id,
            season_id=season.id,
            title="Cloud Solutions Engineer",
            description="Design, deploy, and optimize Azure infrastructure and scalable enterprise cloud services.",
            min_cgpa=7.5,
            max_backlogs=0,
            package_lpa=24.0,
            drive_date=date(2026, 10, 25),
            deadline=date(2026, 10, 22),
            status=JobStatus.PUBLISHED
        )
        job_sde = JobListing(
            company_id=c_amazon.id,
            season_id=season.id,
            title="SDE-1 (Full Stack)",
            description="Develop resilient backend APIs and responsive user interfaces for global consumer services.",
            min_cgpa=7.0,
            max_backlogs=1,
            package_lpa=28.0,
            drive_date=date(2026, 11, 2),
            deadline=date(2026, 10, 30),
            status=JobStatus.PUBLISHED
        )
        job_net = JobListing(
            company_id=c_cisco.id,
            season_id=season.id,
            title="Network Hardware & Systems Engineer",
            description="Silicon, embedded firmware, and high-performance router and switch hardware verification.",
            min_cgpa=7.0,
            max_backlogs=0,
            package_lpa=19.5,
            drive_date=date(2026, 11, 10),
            deadline=date(2026, 11, 5),
            status=JobStatus.PUBLISHED
        )
        session.add_all([job_swe, job_cloud, job_sde, job_net])
        await session.flush()

        # Allowed branches
        session.add_all([
            JobAllowedBranch(job_id=job_swe.id, branch=BranchName.CSE),
            JobAllowedBranch(job_id=job_swe.id, branch=BranchName.ISE),
            JobAllowedBranch(job_id=job_cloud.id, branch=BranchName.CSE),
            JobAllowedBranch(job_id=job_cloud.id, branch=BranchName.ECE),
            JobAllowedBranch(job_id=job_cloud.id, branch=BranchName.ISE),
            # job_sde has no branches -> OPEN TO ALL
            JobAllowedBranch(job_id=job_net.id, branch=BranchName.ECE),
            JobAllowedBranch(job_id=job_net.id, branch=BranchName.CSE),
        ])

        # 5. Students
        # Student 1: High CGPA CSE
        u1 = User(email="student1@college.edu", password_hash=get_password_hash("StudentPass123!"), role=UserRole.STUDENT, is_active=True)
        session.add(u1)
        await session.flush()
        s1 = Student(user_id=u1.id, usn="1MS21CS001", full_name="Aarav Sharma", email="student1@college.edu", branch=BranchName.CSE, cgpa=9.15, active_backlogs=0, cleared_backlogs=0, phone="+91 9876543210")
        session.add(s1)
        await session.flush()
        session.add(StudentConsent(student_id=s1.id, policy_version="1.0", purpose="PLACEMENT_DATA_PROCESSING", is_granted=True))

        # Student 2: ECE with 1 active backlog
        u2 = User(email="student2@college.edu", password_hash=get_password_hash("StudentPass123!"), role=UserRole.STUDENT, is_active=True)
        session.add(u2)
        await session.flush()
        s2 = Student(user_id=u2.id, usn="1MS21EC042", full_name="Priya Patel", email="student2@college.edu", branch=BranchName.ECE, cgpa=7.40, active_backlogs=1, cleared_backlogs=1, phone="+91 9876543211")
        session.add(s2)
        await session.flush()
        session.add(StudentConsent(student_id=s2.id, policy_version="1.0", purpose="PLACEMENT_DATA_PROCESSING", is_granted=True))

        # Student 3: MECH
        u3 = User(email="student3@college.edu", password_hash=get_password_hash("StudentPass123!"), role=UserRole.STUDENT, is_active=True)
        session.add(u3)
        await session.flush()
        s3 = Student(user_id=u3.id, usn="1MS21ME015", full_name="Rohan Varma", email="student3@college.edu", branch=BranchName.MECH, cgpa=8.20, active_backlogs=0, cleared_backlogs=0, phone="+91 9876543212")
        session.add(s3)
        await session.flush()
        session.add(StudentConsent(student_id=s3.id, policy_version="1.0", purpose="PLACEMENT_DATA_PROCESSING", is_granted=True))

        # 6. Applications with various stages for Student 1
        # App 1: OFFERED stage with Microsoft
        app_msft = Application(student_id=s1.id, job_id=job_cloud.id, stage=ApplicationStage.OFFERED, applied_at=datetime.now(timezone.utc) - timedelta(days=10))
        session.add(app_msft)
        await session.flush()

        slot_msft = InterviewSlot(
            application_id=app_msft.id, round_number=1,
            scheduled_time=datetime.now(timezone.utc) - timedelta(days=4),
            venue_or_link="Microsoft Teams Meeting Link",
            status=InterviewStatus.COMPLETED,
            result=InterviewResult.PASSED,
            notes="Strong distributed systems design understanding."
        )
        session.add(slot_msft)

        storage_key = "offer_seed_msft_001"
        offer_file = os.path.join(settings.OFFERS_STORAGE_DIR, f"{storage_key}.pdf")
        os.makedirs(settings.OFFERS_STORAGE_DIR, exist_ok=True)
        with open(offer_file, "wb") as f:
            f.write(b"%PDF-1.4 TalentHub Confidential Offer Letter for Aarav Sharma (1MS21CS001) - Microsoft Cloud Solutions Engineer (24.0 LPA)")

        offer_msft = Offer(
            application_id=app_msft.id,
            package_lpa=24.0,
            issue_date=datetime.now(timezone.utc) - timedelta(days=1),
            acceptance_deadline=datetime.now(timezone.utc) + timedelta(days=7),
            letter_storage_key=storage_key,
            status=OfferStatus.PENDING
        )
        session.add(offer_msft)

        # App 2: INTERVIEW_SCHEDULED stage with Google
        app_google = Application(student_id=s1.id, job_id=job_swe.id, stage=ApplicationStage.INTERVIEW_SCHEDULED, applied_at=datetime.now(timezone.utc) - timedelta(days=5))
        session.add(app_google)
        await session.flush()

        slot_google = InterviewSlot(
            application_id=app_google.id, round_number=1,
            scheduled_time=datetime.now(timezone.utc) + timedelta(days=2, hours=4),
            venue_or_link="Google Meet / CSE Seminar Hall Room 204",
            status=InterviewStatus.SCHEDULED,
            result=InterviewResult.PENDING,
            notes="Round 1: Coding & Algorithms (Two interviewers)"
        )
        session.add(slot_google)

        # App 3: APPLIED stage with Amazon for Student 2
        app_amazon = Application(student_id=s2.id, job_id=job_sde.id, stage=ApplicationStage.APPLIED, applied_at=datetime.now(timezone.utc) - timedelta(days=2))
        session.add(app_amazon)

        await session.commit()
        print("Successfully seeded TalentHub database!")

if __name__ == "__main__":
    asyncio.run(seed())
