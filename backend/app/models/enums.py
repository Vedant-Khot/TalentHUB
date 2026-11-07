from enum import Enum

class UserRole(str, Enum):
    STUDENT = "STUDENT"
    COMPANY_REPRESENTATIVE = "COMPANY_REPRESENTATIVE"
    PLACEMENT_COORDINATOR = "PLACEMENT_COORDINATOR"

class BranchName(str, Enum):
    CSE = "CSE"
    ECE = "ECE"
    ISE = "ISE"
    MECH = "MECH"
    CIVIL = "CIVIL"

class JobStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class ApplicationStage(str, Enum):
    APPLIED = "APPLIED"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    INTERVIEWED = "INTERVIEWED"
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"

class InterviewStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"

class InterviewResult(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"

class OfferStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"

class NotificationChannel(str, Enum):
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"

class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
