import pandas as pd
from sqlalchemy.orm import Session

from ..arrangements.models import ArrangementLog
from ..auth.models import Auth
from ..auth.utils import hash_password
from ..database import SessionLocal
from ..employees.models import Employee
from datetime import datetime
import csv


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
        salt = str(row["email"]).lower()
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
    from ..database import SessionLocal

    db = SessionLocal()
    try:
        with open(file_path, "r") as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                # Convert the update_datetime string to a datetime object
                update_datetime = datetime.strptime(row["update_datetime"], "%Y-%m-%d %H:%M:%S")

                arrangement_log = ArrangementLog(
                    wfh_date=row["wfh_date"],
                    wfh_type=row["wfh_type"],
                    reason_description=row["reason_description"],
                    requester_staff_id=int(row["requester_staff_id"]),
                    approval_status=row["approval_status"],
                    approving_officer=(
                        int(row["approving_officer"]) if row["approving_officer"] else None
                    ),
                    update_datetime=update_datetime,  # Use the converted datetime object
                    batch_id=int(row["batch_id"]) if row["batch_id"] else None,
                )
                db.add(arrangement_log)
        db.commit()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        db.rollback()
    finally:
        db.close()
