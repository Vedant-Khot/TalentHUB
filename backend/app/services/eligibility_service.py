from datetime import datetime, timezone
import json
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.entities import (
    Student, JobListing, PlacementSeason, Application, Offer,
    EligibilityDecision, JobAllowedBranch
)
from app.models.enums import OfferStatus, ApplicationStage

class EligibilityService:
    RULE_VERSION = "1.0"

    @staticmethod
    async def has_accepted_offer_in_season(
        db: AsyncSession,
        student_id: int,
        season_id: int
    ) -> bool:
        """Season-aware accepted-offer check: returns True if student accepted an offer in this season."""
        query = (
            select(Offer)
            .join(Application, Offer.application_id == Application.id)
            .join(JobListing, Application.job_id == JobListing.id)
            .where(
                Application.student_id == student_id,
                JobListing.season_id == season_id,
                Offer.status == OfferStatus.ACCEPTED
            )
        )
        result = await db.execute(query)
        accepted_offer = result.scalar_one_or_none()
        return accepted_offer is not None

    @staticmethod
    async def evaluate_eligibility(
        db: AsyncSession,
        student: Student,
        job: JobListing,
        persist_decision: bool = False
    ) -> dict:
        """
        Single backend eligibility evaluation engine.
        Evaluates rules strictly in order:
        1. student.cgpa >= job.min_cgpa (exact match passes)
        2. student.active_backlogs <= job.max_backlogs (cleared backlogs ignored)
        3. No accepted offer in the applicable placement season
        4. The student's branch is allowed, or the drive has no branch restrictions
        """
        rejection_reasons = []

        # Rule 1: CGPA
        cgpa_pass = student.cgpa >= job.min_cgpa
        if not cgpa_pass:
            rejection_reasons.append(
                f"CGPA {student.cgpa:.2f} is below minimum required {job.min_cgpa:.2f}."
            )

        # Rule 2: Active Backlogs (cleared backlogs must not affect eligibility)
        backlogs_pass = student.active_backlogs <= job.max_backlogs
        if not backlogs_pass:
            rejection_reasons.append(
                f"Active backlogs ({student.active_backlogs}) exceed maximum allowed ({job.max_backlogs})."
            )

        # Rule 3: Season-aware accepted offer rule
        has_offer = await EligibilityService.has_accepted_offer_in_season(
            db=db,
            student_id=student.id,
            season_id=job.season_id
        )
        season_offer_pass = not has_offer
        if not season_offer_pass:
            rejection_reasons.append(
                "You have already accepted an offer in this placement season."
            )

        # Rule 4: Branch restriction (empty job_allowed_branches means open to all)
        # Load allowed branches if not already loaded
        branch_query = select(JobAllowedBranch.branch).where(JobAllowedBranch.job_id == job.id)
        res = await db.execute(branch_query)
        raw_allowed = res.scalars().all()
        allowed_branches_list = [b.value if hasattr(b, "value") else str(b) for b in raw_allowed]
        student_branch_str = student.branch.value if hasattr(student.branch, "value") else str(student.branch)

        if not allowed_branches_list:
            branch_pass = True
        else:
            branch_pass = student_branch_str in allowed_branches_list

        if not branch_pass:
            allowed_branches_str = ", ".join(allowed_branches_list)
            rejection_reasons.append(
                f"Branch {student_branch_str} is not eligible. Allowed branches: {allowed_branches_str}."
            )

        is_eligible = cgpa_pass and backlogs_pass and season_offer_pass and branch_pass

        evaluated_inputs = {
            "student_cgpa": float(student.cgpa),
            "student_active_backlogs": int(student.active_backlogs),
            "student_cleared_backlogs": int(student.cleared_backlogs),
            "student_branch": str(student.branch),
            "job_min_cgpa": float(job.min_cgpa),
            "job_max_backlogs": int(job.max_backlogs),
            "allowed_branches": list(allowed_branches_list),
            "season_id": int(job.season_id)
        }

        if persist_decision:
            decision = EligibilityDecision(
                student_id=student.id,
                job_id=job.id,
                rule_version=EligibilityService.RULE_VERSION,
                is_eligible=is_eligible,
                cgpa_pass=cgpa_pass,
                backlogs_pass=backlogs_pass,
                season_offer_pass=season_offer_pass,
                branch_pass=branch_pass,
                rejection_reasons=json.dumps(rejection_reasons),
                evaluated_inputs=json.dumps(evaluated_inputs),
                evaluated_at=datetime.now(timezone.utc)
            )
            db.add(decision)
            # Commit will be handled by the caller transaction

        return {
            "is_eligible": is_eligible,
            "cgpa_pass": cgpa_pass,
            "backlogs_pass": backlogs_pass,
            "season_offer_pass": season_offer_pass,
            "branch_pass": branch_pass,
            "rejection_reasons": rejection_reasons,
            "inputs_evaluated": evaluated_inputs
        }
