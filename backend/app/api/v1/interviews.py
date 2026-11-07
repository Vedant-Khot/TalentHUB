from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.api.deps import require_roles
from app.models.entities import User
from app.models.enums import UserRole, InterviewResult
from app.schemas.application import (
    InterviewScheduleRequest, InterviewRescheduleRequest,
    InterviewResultUpdateRequest, InterviewSlotResponse
)
from app.services.interview_and_offer_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["Interviews"])

@router.post("/{application_id}/schedule", response_model=InterviewSlotResponse, status_code=status.HTTP_201_CREATED)
async def schedule_interview_round(
    application_id: int,
    data: InterviewScheduleRequest,
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    slot = await InterviewService.schedule_round(
        db=db,
        application_id=application_id,
        round_number=data.round_number,
        scheduled_time=data.scheduled_time,
        venue_or_link=data.venue_or_link,
        actor_user_id=coordinator.id,
        notes=data.notes
    )
    return slot

@router.put("/slots/{slot_id}/reschedule", response_model=InterviewSlotResponse)
async def reschedule_interview_round(
    slot_id: int,
    data: InterviewRescheduleRequest,
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    slot = await InterviewService.reschedule_round(
        db=db,
        slot_id=slot_id,
        new_time=data.scheduled_time,
        venue_or_link=data.venue_or_link,
        notes=data.notes
    )
    return slot

@router.put("/slots/{slot_id}/result", response_model=InterviewSlotResponse)
async def record_interview_result(
    slot_id: int,
    data: InterviewResultUpdateRequest,
    mark_all_rounds_complete: bool = False,
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    slot = await InterviewService.record_result(
        db=db,
        slot_id=slot_id,
        result=data.result,
        actor_user_id=coordinator.id,
        notes=data.notes,
        mark_all_rounds_complete=mark_all_rounds_complete
    )
    return slot
