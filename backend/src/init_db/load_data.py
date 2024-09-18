import pandas as pd
from sqlalchemy.orm import Session
from ..employees.models import Employee
from ...database import SessionLocal


def load_employee_data_from_csv(file_path: str):
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Create a new database session
    db: Session = SessionLocal()

    # Iterate over the DataFrame and insert data into the database
    for _, row in df.iterrows():
        employee = Employee(
            staff_id=row["Staff_ID"],
            staff_fname=row["Staff_FName"],
            staff_lname=row["Staff_LName"],
            dept=row["Dept"],
            position=row["Position"],
            country=row["Country"],
            email=row["Email"],
            reporting_manager=row["Reporting_Manager"],
            role=row["Role"],
        )
        db.add(employee)

    # Commit the transaction
    db.commit()

    # Close the session
    db.close()
