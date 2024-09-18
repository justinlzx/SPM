import pandas as pd
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..employees.models import Employee
from ..auth.models import Auth
from ..auth.utils import hash_password

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
        # Hash the password using staff_id as the salt
        salt = str(row["Staff_ID"])  # Use the staff_id as the salt
        hashed_password = hash_password(row["unhashed_password"], salt)

        # Create a Auth entry in the database
        auth = Auth(
            staff_id=row["Staff_ID"],
            email=row["email"],
            hashed_password=hashed_password
        )
        db.add(auth)

    # Commit the transaction
    db.commit()

    # Close the session
    db.close()