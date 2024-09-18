from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthCheck(BaseModel):
    status: str
    version: str


@router.get("/", response_model=HealthCheck)
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
