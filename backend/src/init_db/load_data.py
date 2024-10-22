import csv
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from ..arrangements.models import ArrangementLog, LatestArrangement
from ..auth.models import Auth
from ..auth.utils import hash_password
from ..database import SessionLocal
from ..employees.models import Employee


# Function to load employee data from employee.csv
def load_employee_data_from_csv(file_path: str):
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{file_path}' is empty.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading '{file_path}': {str(e)}")
        return

    # Create a new database session
    db: Session = SessionLocal()

    try:
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
    except Exception as e:
        print(f"An error occurred while loading employee data: {str(e)}")
        db.rollback()
    finally:
        # Close the session
        db.close()


# Function to load auth data from auth.csv
def load_auth_data_from_csv(file_path: str):
    try:
        # Read the CSV file for authentication data
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{file_path}' is empty.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading '{file_path}': {str(e)}")
        return

    # Create a new database session
    db: Session = SessionLocal()

    try:
        # Iterate over the DataFrame and insert data into the 'auth' table
        for _, row in df.iterrows():
            # Hash the password using email as the salt
            salt = str(row["email"]).lower()
            hashed_password = hash_password(row["unhashed_password"], salt)

            # Create an Auth entry in the database
            auth = Auth(
                email=row["email"],
                hashed_password=hashed_password,
            )
            db.add(auth)

        # Commit the transaction
        db.commit()
    except Exception as e:
        print(f"An error occurred while loading auth data: {str(e)}")
        db.rollback()
    finally:
        # Close the session
        db.close()


def load_latest_arrangement_data_from_csv(file_path: str):
    db = SessionLocal()
    try:
        # Check for empty file using pandas before processing the CSV
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                print(f"Error: The file '{file_path}' is empty.")
                return
        except pd.errors.EmptyDataError:
            print(f"Error: The file '{file_path}' is empty.")
            return

        # Process CSV data as expected
        with open(file_path, "r") as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                try:
                    # Convert the update_datetime string to a datetime object
                    update_datetime = datetime.strptime(
                        row["update_datetime"], "%Y-%m-%dT%H:%M:%SZ"
                    )

                    latest_arrangement = LatestArrangement(
                        wfh_date=row["wfh_date"],
                        wfh_type=row["wfh_type"],
                        reason_description=row["reason_description"],
                        requester_staff_id=int(row["requester_staff_id"]),
                        current_approval_status=row["current_approval_status"],
                        approving_officer=(
                            int(row["approving_officer"]) if row["approving_officer"] else None
                        ),
                        update_datetime=update_datetime,
                        batch_id=int(row["batch_id"]) if row["batch_id"] else None,
                        supporting_doc_1=None,
                        supporting_doc_2=None,
                        supporting_doc_3=None,
                        latest_log_id=row["latest_log_id"],
                    )
                    db.add(latest_arrangement)
                except KeyError as ke:
                    print(f"Missing expected column in CSV: {str(ke)}")
                except ValueError as ve:
                    print(f"Data conversion error: {str(ve)}")
                except Exception as e:
                    print(f"An unexpected error occurred while processing row: {str(e)}")
                    # Handle errors for specific rows without rolling back the entire transaction
                    continue

        # Commit all valid rows after processing
        db.commit()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        db.rollback()  # Rollback if there's a major issue
    finally:
        db.close()
