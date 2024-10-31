from fastapi import APIRouter
from pydantic import BaseModel

from ..logger import logger

router = APIRouter()


class HealthCheck(BaseModel):
    status: str
    version: str


@router.get("/", response_model=HealthCheck)
def health_check():
    logger.info("Received Health Check. Health Check OK")
    return {"status": "healthy", "version": "1.0.0"}
