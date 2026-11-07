from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from app.models.enums import BranchName, JobStatus

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    website: Optional[str] = None
    contact_email: Optional[str] = None
    description: Optional[str] = None

class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website: Optional[str] = None
    contact_email: Optional[str] = None
    description: Optional[str] = None

class PlacementSeasonCreate(BaseModel):
    year: int
    name: str
    is_active: bool = True
    start_date: date
    end_date: date

class PlacementSeasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    name: str
    is_active: bool
    start_date: date
    end_date: date

class JobCreate(BaseModel):
    company_id: int
    season_id: int
    title: str = Field(..., min_length=2, max_length=150)
    description: str
    min_cgpa: float = Field(0.0, ge=0.0, le=10.0)
    max_backlogs: int = Field(0, ge=0)
    package_lpa: float = Field(0.0, ge=0.0)
    drive_date: date
    deadline: date
    allowed_branches: List[BranchName] = []  # Empty means open to all branches
    status: JobStatus = JobStatus.DRAFT

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    min_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    max_backlogs: Optional[int] = Field(None, ge=0)
    package_lpa: Optional[float] = Field(None, ge=0.0)
    drive_date: Optional[date] = None
    deadline: Optional[date] = None
    allowed_branches: Optional[List[BranchName]] = None
    status: Optional[JobStatus] = None

class EligibilityCheckResult(BaseModel):
    is_eligible: bool
    cgpa_pass: bool
    backlogs_pass: bool
    season_offer_pass: bool
    branch_pass: bool
    rejection_reasons: List[str]
    inputs_evaluated: dict

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    company_name: str
    season_id: int
    season_name: str
    title: str
    description: str
    min_cgpa: float
    max_backlogs: int
    package_lpa: float
    drive_date: date
    deadline: date
    status: JobStatus
    allowed_branches: List[str]
    is_open_to_all_branches: bool
    eligibility: Optional[EligibilityCheckResult] = None
    has_applied: bool = False
    application_stage: Optional[str] = None
