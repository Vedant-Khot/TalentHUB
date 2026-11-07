import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.api.deps import require_roles, get_current_user
from app.models.entities import User, Offer, Application, Student
from app.models.enums import UserRole
from app.schemas.application import OfferCreateRequest, OfferActionRequest, OfferResponse
from app.services.interview_and_offer_service import OfferService
from app.core.config import settings

router = APIRouter(prefix="/offers", tags=["Offers"])

@router.post("/{application_id}/create", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    application_id: int,
    data: OfferCreateRequest,
    coordinator: User = Depends(require_roles([UserRole.PLACEMENT_COORDINATOR])),
    db: AsyncSession = Depends(get_db)
):
    offer = await OfferService.create_offer(
        db=db,
        application_id=application_id,
        package_lpa=data.package_lpa,
        actor_user_id=coordinator.id,
        acceptance_deadline=data.acceptance_deadline
    )
    return offer

@router.post("/{offer_id}/respond", response_model=OfferResponse)
async def respond_to_offer(
    offer_id: int,
    data: OfferActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    offer = await OfferService.respond_to_offer(
        db=db,
        offer_id=offer_id,
        student_user_id=current_user.id,
        action=data.action
    )
    return offer

@router.get("/{offer_id}/letter")
async def download_offer_letter(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    offer_query = (
        select(Offer)
        .options(selectinload(Offer.application).selectinload(Application.student))
        .where(Offer.id == offer_id)
    )
    res = await db.execute(offer_query)
    offer = res.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")

    # Authorization check: only owning student or coordinator
    if current_user.role == UserRole.STUDENT:
        if offer.application.student.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view or download this offer letter."
            )
    elif current_user.role != UserRole.PLACEMENT_COORDINATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden."
        )

    file_path = os.path.join(settings.OFFERS_STORAGE_DIR, f"{offer.letter_storage_key}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer letter file not found in storage.")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"Offer_Letter_{offer.application.student.usn}.pdf"
    )
