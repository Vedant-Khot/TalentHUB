from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from app.models.enums import BranchName

class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    usn: str
    full_name: str
    email: EmailStr
    branch: BranchName
    cgpa: float
    active_backlogs: int
    cleared_backlogs: int
    phone: Optional[str] = None
    has_active_consent: bool = True
    accepted_offer_this_season: bool = False

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    active_backlogs: Optional[int] = Field(None, ge=0)
    cleared_backlogs: Optional[int] = Field(None, ge=0)
