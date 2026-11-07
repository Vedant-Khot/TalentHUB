from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import User, Student
from app.models.enums import UserRole
from app.core.security import verify_password, get_password_hash, create_access_token
from app.schemas.auth import StudentRegisterRequest
from app.services.consent_service import ConsentService

class AuthService:
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str
    ) -> User:
        normalized_email = email.strip().lower()
        query = (
            select(User)
            .options(selectinload(User.student))
            .where(User.email == normalized_email)
        )
        res = await db.execute(query)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled."
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password."
            )

        return user

    @staticmethod
    async def register_student(
        db: AsyncSession,
        data: StudentRegisterRequest
    ) -> Tuple[User, Student]:
        normalized_email = data.email.strip().lower()
        normalized_usn = data.usn.strip().upper()

        # Check existing user email
        existing_user_res = await db.execute(select(User).where(User.email == normalized_email))
        if existing_user_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists."
            )

        # Check existing student USN
        existing_usn_res = await db.execute(select(Student).where(Student.usn == normalized_usn))
        if existing_usn_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A student with this USN already exists."
            )

        # Create user
        user = User(
            email=normalized_email,
            password_hash=get_password_hash(data.password),
            role=UserRole.STUDENT,
            is_active=True
        )
        db.add(user)
        await db.flush()

        # Create student profile
        student = Student(
            user_id=user.id,
            usn=normalized_usn,
            full_name=data.full_name.strip(),
            email=normalized_email,
            branch=data.branch,
            cgpa=data.cgpa,
            active_backlogs=data.active_backlogs,
            cleared_backlogs=data.cleared_backlogs,
            phone=data.phone.strip() if data.phone else None
        )
        db.add(student)
        await db.flush()

        # Record consent if provided
        if data.consent_granted:
            await ConsentService.record_consent(
                db=db,
                student_id=student.id,
                policy_version="1.0",
                purpose="PLACEMENT_DATA_PROCESSING",
                is_granted=True
            )

        await db.commit()
        await db.refresh(user)
        await db.refresh(student)
        return user, student
