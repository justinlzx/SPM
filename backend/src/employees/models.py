from sqlalchemy.orm import Session
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import engine
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


if __name__ == "__main__":

    session = Session(bind=engine)

    director = Employee(
        staff_id=3,
        staff_fname="Johnson",
        staff_lname="Doe",
        email="johnson.doe@test.com",
        dept="IT",
        position="Director",
        country="USA",
        role=2,
    )

    session.add(director)
    session.commit()

    manager = Employee(
        staff_id=1,
        staff_fname="Jane",
        staff_lname="Smith",
        email="jane.smith@test.com",
        dept="IT",
        position="Manager",
        country="USA",
        role=2,
        reporting_manager=3,
    )

    session.add(manager)
    session.commit()

    employee = Employee(
        staff_fname="John",
        staff_lname="Doe",
        email="john.doe@test.com",
        dept="IT",
        position="Manager",
        country="USA",
        reporting_manager=1,
        role=3,
    )

    session.add(employee)
    session.commit()

    session.refresh(employee)

    # Print the manager object
    print(employee.manager.staff_fname)
    print(manager.manager.staff_fname)

    # Close the session
    session.close()
