from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import UserLoginRequest, TokenResponse, StudentRegisterRequest, UserResponse
from app.services.auth_service import AuthService
from app.core.security import create_access_token
from app.api.deps import get_current_user
from app.models.entities import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.authenticate_user(db, login_data.email, login_data.password)
    token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role, "email": user.email}
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        student_id=user.student.id if user.student else None,
        company_id=user.company_id
    )

@router.post("/register-student", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_student(
    register_data: StudentRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    user, student = await AuthService.register_student(db, register_data)
    token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role, "email": user.email}
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        student_id=student.id,
        company_id=None
    )

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        student_id=current_user.student.id if current_user.student else None,
        company_id=current_user.company_id
    )
