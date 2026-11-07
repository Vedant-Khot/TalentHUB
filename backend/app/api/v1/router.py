from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.students import router as students_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.applications import router as applications_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.offers import router as offers_router
from app.api.v1.coordinator import router as coordinator_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(jobs_router)
api_router.include_router(applications_router)
api_router.include_router(interviews_router)
api_router.include_router(offers_router)
api_router.include_router(coordinator_router)

@api_router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "TalentHub API", "version": "1.0.0"}
