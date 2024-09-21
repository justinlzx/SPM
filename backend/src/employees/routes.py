from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter()


@router.get("/manager/peer/{staff_id}")
def get_reporting_manager(staff_id: int, db: Session = Depends(get_db)):
    return staff_id
