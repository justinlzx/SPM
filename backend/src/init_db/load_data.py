import pandas as pd
from sqlalchemy.orm import Session

from ..arrangements.models import ArrangementLog
from ..auth.models import Auth
from ..auth.utils import hash_password
from ..database import SessionLocal
from ..employees.models import Employee


# Function to load employee data from employee.csv
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


# Function to load auth data from auth.csv
def load_auth_data_from_csv(file_path: str):
    # Read the CSV file for authentication data
    df = pd.read_csv(file_path)

    # Create a new database session
    db: Session = SessionLocal()

    # Iterate over the DataFrame and insert data into the 'auth' table
    for _, row in df.iterrows():
        # Hash the password using email as the salt
        salt = str(row["email"])
        hashed_password = hash_password(row["unhashed_password"], salt)

        # Create a Auth entry in the database
        auth = Auth(
            email=row["email"],
            hashed_password=hashed_password,
        )
        db.add(auth)

    # Commit the transaction
    db.commit()

    # Close the session
    db.close()


# Function to load auth data from arrangements.csv
def load_arrangement_data_from_csv(file_path: str):
    # Read the CSV file for authentication data
    df = pd.read_csv(file_path)

    # Create a new database session
    db: Session = SessionLocal()

    # Iterate over the DataFrame and insert arrangement data into the database
    for _, row in df.iterrows():
        arrangement_log = ArrangementLog(
            update_datetime=row["update_datetime"],
            requester_staff_id=row["requester_staff_id"],
            wfh_date=row["wfh_date"],
            wfh_type=row["wfh_type"],
            approval_status=row["approval_status"],
            approving_officer=row.get(
                "approving_officer"
            ),  # Use .get() to handle NaN values
            reason_description=row["reason_description"],
            batch_id=row.get("batch_id"),  # Use .get() to handle NaN values
        )
        db.add(arrangement_log)

    # Commit the transaction
    db.commit()

    # Close the session
    db.close()
