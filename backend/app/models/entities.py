from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, Date, DateTime, Text, JSON,
    ForeignKey, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, utc_now
from app.models.enums import (
    UserRole, BranchName, JobStatus, ApplicationStage,
    InterviewStatus, InterviewResult, OfferStatus,
    NotificationChannel, NotificationStatus
)

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    student: Mapped[Optional["Student"]] = relationship("Student", back_populates="user", uselist=False)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="representatives")
    notifications: Mapped[List["NotificationLog"]] = relationship("NotificationLog", back_populates="user")

    __table_args__ = (
        CheckConstraint(
            "role IN ('STUDENT', 'COMPANY_REPRESENTATIVE', 'PLACEMENT_COORDINATOR')",
            name="ck_users_valid_role"
        ),
    )


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    usn: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    branch: Mapped[BranchName] = mapped_column(String(10), nullable=False, index=True)
    cgpa: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    active_backlogs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cleared_backlogs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="student")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="student", cascade="all, delete-orphan")
    consents: Mapped[List["StudentConsent"]] = relationship("StudentConsent", back_populates="student", cascade="all, delete-orphan")
    eligibility_decisions: Mapped[List["EligibilityDecision"]] = relationship("EligibilityDecision", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("branch IN ('CSE', 'ECE', 'ISE', 'MECH', 'CIVIL')", name="ck_students_valid_branch"),
        CheckConstraint("cgpa >= 0.0 AND cgpa <= 10.0", name="ck_students_cgpa_range"),
        CheckConstraint("active_backlogs >= 0", name="ck_students_active_backlogs_nonneg"),
        CheckConstraint("cleared_backlogs >= 0", name="ck_students_cleared_backlogs_nonneg"),
    )


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    job_listings: Mapped[List["JobListing"]] = relationship("JobListing", back_populates="company", cascade="all, delete-orphan")
    representatives: Mapped[List["User"]] = relationship("User", back_populates="company")


class PlacementSeason(Base, TimestampMixin):
    __tablename__ = "placement_seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    job_listings: Mapped[List["JobListing"]] = relationship("JobListing", back_populates="season", cascade="all, delete-orphan")


class JobListing(Base, TimestampMixin):
    __tablename__ = "job_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    season_id: Mapped[int] = mapped_column(Integer, ForeignKey("placement_seasons.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    min_cgpa: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_backlogs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    package_lpa: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    drive_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[JobStatus] = mapped_column(String(20), default=JobStatus.DRAFT, nullable=False, index=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="job_listings")
    season: Mapped["PlacementSeason"] = relationship("PlacementSeason", back_populates="job_listings")
    allowed_branches: Mapped[List["JobAllowedBranch"]] = relationship("JobAllowedBranch", back_populates="job", cascade="all, delete-orphan")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    eligibility_decisions: Mapped[List["EligibilityDecision"]] = relationship("EligibilityDecision", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("min_cgpa >= 0.0 AND min_cgpa <= 10.0", name="ck_jobs_min_cgpa_range"),
        CheckConstraint("max_backlogs >= 0", name="ck_jobs_max_backlogs_nonneg"),
        CheckConstraint("package_lpa >= 0.0", name="ck_jobs_package_lpa_nonneg"),
        CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'CLOSED', 'CANCELLED')", name="ck_jobs_valid_status"),
    )


class JobAllowedBranch(Base):
    __tablename__ = "job_allowed_branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    branch: Mapped[BranchName] = mapped_column(String(10), nullable=False)

    # Relationships
    job: Mapped["JobListing"] = relationship("JobListing", back_populates="allowed_branches")

    __table_args__ = (
        UniqueConstraint("job_id", "branch", name="uq_job_allowed_branch"),
        CheckConstraint("branch IN ('CSE', 'ECE', 'ISE', 'MECH', 'CIVIL')", name="ck_job_allowed_branch_valid"),
    )


class StudentConsent(Base):
    __tablename__ = "student_consents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_version: Mapped[str] = mapped_column(String(20), nullable=False)
    purpose: Mapped[str] = mapped_column(String(100), nullable=False)
    is_granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="consents")


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    stage: Mapped[ApplicationStage] = mapped_column(String(30), default=ApplicationStage.APPLIED, nullable=False, index=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="applications")
    job: Mapped["JobListing"] = relationship("JobListing", back_populates="applications")
    interview_slots: Mapped[List["InterviewSlot"]] = relationship("InterviewSlot", back_populates="application", cascade="all, delete-orphan", order_by="InterviewSlot.round_number")
    offer: Mapped[Optional["Offer"]] = relationship("Offer", back_populates="application", uselist=False, cascade="all, delete-orphan")
    status_history: Mapped[List["ApplicationStatusHistory"]] = relationship("ApplicationStatusHistory", back_populates="application", cascade="all, delete-orphan", order_by="ApplicationStatusHistory.changed_at.desc()")

    __table_args__ = (
        UniqueConstraint("student_id", "job_id", name="uq_application_student_job"),
        CheckConstraint(
            "stage IN ('APPLIED', 'SHORTLISTED', 'INTERVIEW_SCHEDULED', 'INTERVIEWED', 'OFFERED', 'ACCEPTED')",
            name="ck_applications_valid_stage"
        ),
        Index("idx_app_student_stage", "student_id", "stage"),
        Index("idx_app_job_stage", "job_id", "stage"),
    )


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    from_stage: Mapped[str] = mapped_column(String(30), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="status_history")
    changed_by: Mapped[Optional["User"]] = relationship("User")


class InterviewSlot(Base, TimestampMixin):
    __tablename__ = "interview_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    round_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    venue_or_link: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[InterviewStatus] = mapped_column(String(20), default=InterviewStatus.SCHEDULED, nullable=False)
    result: Mapped[InterviewResult] = mapped_column(String(20), default=InterviewResult.PENDING, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="interview_slots")

    __table_args__ = (
        UniqueConstraint("application_id", "round_number", name="uq_interview_app_round"),
        CheckConstraint("round_number >= 1", name="ck_interview_round_number_positive"),
        CheckConstraint("status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED', 'RESCHEDULED')", name="ck_interview_valid_status"),
        CheckConstraint("result IN ('PENDING', 'PASSED', 'FAILED')", name="ck_interview_valid_result"),
        Index("idx_interview_upcoming", "scheduled_time", "status"),
    )


class Offer(Base, TimestampMixin):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False)
    package_lpa: Mapped[float] = mapped_column(Float, nullable=False)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    acceptance_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    letter_storage_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[OfferStatus] = mapped_column(String(20), default=OfferStatus.PENDING, nullable=False, index=True)
    response_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="offer")

    __table_args__ = (
        CheckConstraint("package_lpa >= 0.0", name="ck_offers_package_lpa_nonneg"),
        CheckConstraint("status IN ('PENDING', 'ACCEPTED', 'DECLINED')", name="ck_offers_valid_status"),
    )


class EligibilityDecision(Base):
    __tablename__ = "eligibility_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    is_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    cgpa_pass: Mapped[bool] = mapped_column(Boolean, nullable=False)
    backlogs_pass: Mapped[bool] = mapped_column(Boolean, nullable=False)
    season_offer_pass: Mapped[bool] = mapped_column(Boolean, nullable=False)
    branch_pass: Mapped[bool] = mapped_column(Boolean, nullable=False)
    rejection_reasons: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    evaluated_inputs: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="eligibility_decisions")
    job: Mapped["JobListing"] = relationship("JobListing", back_populates="eligibility_decisions")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[NotificationChannel] = mapped_column(String(20), default=NotificationChannel.EMAIL, nullable=False)
    template_name: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    status: Mapped[NotificationStatus] = mapped_column(String(20), default=NotificationStatus.PENDING, nullable=False, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    __table_args__ = (
        CheckConstraint("channel IN ('EMAIL', 'IN_APP')", name="ck_notifications_valid_channel"),
        CheckConstraint("status IN ('PENDING', 'SENT', 'FAILED')", name="ck_notifications_valid_status"),
        Index("idx_notifications_retry", "status", "retry_count"),
    )
