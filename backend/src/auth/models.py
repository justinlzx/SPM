from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from ..database import Base


class Auth(Base):
    __tablename__ = "auth"

    staff_id = Column(Integer, primary_key=True, index=True, unique=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


def create_user(db: Session, staff_id: int, email: str, hashed_password: str):
    new_user = Auth(staff_id=staff_id, email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_email(db: Session, email: str):
    return db.query(Auth).filter(Auth.email == email).first()


def get_user_by_staff_id(db: Session, staff_id: int):
    return db.query(Auth).filter(Auth.staff_id == staff_id).first()
