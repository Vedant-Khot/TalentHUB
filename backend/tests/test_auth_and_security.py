import pytest
import pytest_asyncio
from datetime import date
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event

from app.db.base import Base
from app.db.session import get_db
from app.models.entities import User, Student, Company, PlacementSeason, JobListing, Application, Offer
from app.models.enums import UserRole, BranchName, JobStatus, ApplicationStage, OfferStatus
from app.core.security import get_password_hash, verify_password, create_access_token
from app.main import app

@pytest_asyncio.fixture
async def app_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncSessionLocal() as session:
        # Seed test users
        coord_user = User(
            email="admin@college.edu",
            password_hash=get_password_hash("AdminPass123!"),
            role=UserRole.PLACEMENT_COORDINATOR,
            is_active=True
        )
        student_user = User(
            email="student@college.edu",
            password_hash=get_password_hash("StudentPass123!"),
            role=UserRole.STUDENT,
            is_active=True
        )
        disabled_user = User(
            email="disabled@college.edu",
            password_hash=get_password_hash("DisabledPass123!"),
            role=UserRole.STUDENT,
            is_active=False
        )
        other_student_user = User(
            email="other@college.edu",
            password_hash=get_password_hash("OtherPass123!"),
            role=UserRole.STUDENT,
            is_active=True
        )
        session.add_all([coord_user, student_user, disabled_user, other_student_user])
        await session.commit()

        student = Student(
            user_id=student_user.id,
            usn="1MS21CS501",
            full_name="Student Test",
            email="student@college.edu",
            branch=BranchName.CSE,
            cgpa=9.0
        )
        other_student = Student(
            user_id=other_student_user.id,
            usn="1MS21CS502",
            full_name="Other Student",
            email="other@college.edu",
            branch=BranchName.CSE,
            cgpa=8.0
        )
        company = Company(name="Tesla")
        season = PlacementSeason(year=2026, name="2026 Season", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        session.add_all([student, other_student, company, season])
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

def test_argon2id_password_hashing():
    raw = "MySuperSecretPassword#2026"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

@pytest.mark.asyncio
async def test_login_flow_and_deactivated_account(app_client: AsyncClient):
    # Valid login
    res = await app_client.post("/api/v1/auth/login", json={
        "email": "student@college.edu",
        "password": "StudentPass123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "STUDENT"

    # Invalid password
    res_bad = await app_client.post("/api/v1/auth/login", json={
        "email": "student@college.edu",
        "password": "WrongPassword"
    })
    assert res_bad.status_code == 401

    # Deactivated account
    res_disabled = await app_client.post("/api/v1/auth/login", json={
        "email": "disabled@college.edu",
        "password": "DisabledPass123!"
    })
    assert res_disabled.status_code == 403
    assert "disabled" in res_disabled.json()["detail"].lower()

@pytest.mark.asyncio
async def test_role_based_access_control(app_client: AsyncClient):
    # Login as Student
    s_res = await app_client.post("/api/v1/auth/login", json={
        "email": "student@college.edu",
        "password": "StudentPass123!"
    })
    student_token = s_res.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Student attempts to post a drive (Coordinator only) -> 403
    drive_payload = {
        "company_id": 1,
        "season_id": 1,
        "title": "Unauthorized Drive",
        "description": "Desc",
        "min_cgpa": 7.0,
        "max_backlogs": 0,
        "package_lpa": 12.0,
        "drive_date": "2026-10-30",
        "deadline": "2026-10-29",
        "allowed_branches": []
    }
    unauth_res = await app_client.post("/api/v1/jobs/", json=drive_payload, headers=student_headers)
    assert unauth_res.status_code == 403

    # Coordinator can post drive -> 201
    c_res = await app_client.post("/api/v1/auth/login", json={
        "email": "admin@college.edu",
        "password": "AdminPass123!"
    })
    coord_token = c_res.json()["access_token"]
    coord_headers = {"Authorization": f"Bearer {coord_token}"}

    auth_res = await app_client.post("/api/v1/jobs/", json=drive_payload, headers=coord_headers)
    assert auth_res.status_code == 201
