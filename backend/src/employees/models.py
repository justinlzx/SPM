from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class Employee(Base):
    __tablename__ = "employees"

    staff_id = Column(Integer, primary_key=True)
    staff_fname = Column(String(length=50), nullable=False)
    staff_lname = Column(String(length=50), nullable=False)
    dept = Column(String(length=50), nullable=False)
    position = Column(String(length=50), nullable=False)
    country = Column(String(length=50), nullable=False)
    email = Column(String, unique=True, nullable=False)
    reporting_manager = Column(Integer, ForeignKey("employees.staff_id"))
    role = Column(Integer, CheckConstraint("role IN (1, 2, 3)"), nullable=False)

    manager = relationship("Employee", remote_side=[staff_id])
