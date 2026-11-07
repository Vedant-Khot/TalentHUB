from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from app.models.enums import UserRole, BranchName

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: UserRole
    student_id: Optional[int] = None
    company_id: Optional[int] = None

class StudentRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    usn: str = Field(..., min_length=5, max_length=20)
    full_name: str = Field(..., min_length=2, max_length=100)
    branch: BranchName
    cgpa: float = Field(..., ge=0.0, le=10.0)
    active_backlogs: int = Field(0, ge=0)
    cleared_backlogs: int = Field(0, ge=0)
    phone: Optional[str] = None
    consent_granted: bool = True

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: UserRole
    is_active: bool
    student_id: Optional[int] = None
    company_id: Optional[int] = None

class ConsentRequest(BaseModel):
    policy_version: str = "1.0"
    purpose: str = "PLACEMENT_DATA_PROCESSING"
    is_granted: bool

class ConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    policy_version: str
    purpose: str
    is_granted: bool
    event_timestamp: str
