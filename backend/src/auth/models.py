from sqlalchemy import Column, String
from sqlalchemy.orm import Session, relationship

from ..database import Base
from ..employees.models import Employee


class Auth(Base):
    __tablename__ = "auth"

    email = Column(String, primary_key=True, unique=True, index=True)
    hashed_password = Column(String)

    employee = relationship("Employee", back_populates="auth_info")


def create_user(db: Session, email: str, hashed_password: str):
    new_user = Auth(email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_email(db: Session, email: str):
    return (
        db.query(Auth)
        .join(Employee, Auth.email == Employee.email, isouter=False)
        .filter(Auth.email == email)
        .first()
    )
