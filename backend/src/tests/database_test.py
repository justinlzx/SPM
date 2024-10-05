import pytest
from unittest.mock import MagicMock
import pandas as pd
from sqlalchemy.orm import Session
from src.init_db.load_data import (
    load_employee_data_from_csv,
    load_auth_data_from_csv,
    load_arrangement_data_from_csv,
)
from ..auth.utils import hash_password
from datetime import datetime
import os
from unittest.mock import mock_open
import csv


@pytest.fixture
def mock_db_session(mocker):
    # Mock the session to avoid real database writes
    session = MagicMock(spec=Session)
    mocker.patch("src.init_db.load_data.SessionLocal", return_value=session)
    return session


def test_load_employee_data_from_csv(mock_db_session):
    load_employee_data_from_csv("src/tests/test_employee.csv")
    assert mock_db_session.add.call_count == 554
    df = pd.read_csv("src/tests/test_employee.csv")
    actual_employees = [call[0][0] for call in mock_db_session.add.call_args_list]

    for i, row in df.iterrows():
        # compare each attribute in actual_employees
        # the key is different
        assert any(
            [
                employee.staff_id == row["Staff_ID"]
                and employee.staff_fname == row["Staff_FName"]
                and employee.staff_lname == row["Staff_LName"]
                and employee.dept == row["Dept"]
                and employee.position == row["Position"]
                and employee.country == row["Country"]
                and employee.email == row["Email"]
                and employee.reporting_manager == row["Reporting_Manager"]
                and employee.role == row["Role"]
                for employee in actual_employees
            ]
        )

    mock_db_session.commit.assert_called_once()
    mock_db_session.close.assert_called_once()


def test_load_auth_data_from_csv(mock_db_session):
    # Call the function to load auth data from the CSV
    load_auth_data_from_csv("src/tests/test_auth.csv")

    # Check that the correct number of records have been added to the database
    assert mock_db_session.add.call_count == 554

    # Read the CSV file to verify data
    df = pd.read_csv("src/tests/test_auth.csv")
    actual_auths = [call[0][0] for call in mock_db_session.add.call_args_list]

    for i, row in df.iterrows():
        # Check that each Auth object is created with the correct hashed password
        salt = row["email"].lower()
        expected_hashed_password = hash_password(row["unhashed_password"], salt)
        assert any(
            [
                auth.email == row["email"] and auth.hashed_password == expected_hashed_password
                for auth in actual_auths
            ]
        )

    # Ensure commit and close are called
    mock_db_session.commit.assert_called_once()
    mock_db_session.close.assert_called_once()


def test_load_arrangement_data_from_csv(mock_db_session, mocker):
    # Get the directory of the current test file
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the CSV file
    csv_path = os.path.join(current_dir, "test_arrangement.csv")

    # Ensure the file exists
    assert os.path.exists(csv_path), f"Test file not found: {csv_path}"

    # Read the actual CSV file
    df = pd.read_csv(csv_path)

    # Mock the ArrangementLog model
    mock_arrangement_log = mocker.patch("src.init_db.load_data.ArrangementLog")

    # Call the function with the actual CSV path
    load_arrangement_data_from_csv(csv_path)

    # Check that the correct number of ArrangementLog objects were added to the session
    assert mock_db_session.add.call_count == len(
        df
    ), f"Expected {len(df)} calls to session.add, but got {mock_db_session.add.call_count}"

    # Verify the calls to ArrangementLog
    for i, row in df.iterrows():
        mock_arrangement_log.assert_any_call(
            update_datetime=datetime.strptime(row["update_datetime"], "%Y-%m-%d %H:%M:%S"),
            requester_staff_id=row["requester_staff_id"],
            wfh_date=row["wfh_date"],
            wfh_type=row["wfh_type"],
            approval_status=row["approval_status"],
            approving_officer=(
                row["approving_officer"] if pd.notna(row["approving_officer"]) else None
            ),
            reason_description=row["reason_description"],
            batch_id=row["batch_id"] if pd.notna(row["batch_id"]) else None,
        )

    # Verify that commit and close were called on the session
    mock_db_session.commit.assert_called_once()
    mock_db_session.close.assert_called_once()


def test_load_arrangement_data_from_csv_exception(mock_db_session, mocker, capsys):
    # Mock the ArrangementLog model to raise an exception during instantiation
    mocker.patch("src.init_db.load_data.ArrangementLog", side_effect=Exception("Test Exception"))

    # Call the function with a mock CSV path
    load_arrangement_data_from_csv("src/tests/test_arrangement.csv")

    # Capture the stdout to check for the error message
    captured = capsys.readouterr()
    assert "An error occurred: Test Exception" in captured.out

    # Ensure rollback is called due to exception
    mock_db_session.rollback.assert_called_once()
    # Ensure commit is not called
    mock_db_session.commit.assert_not_called()
    # Ensure the session is closed after exception
    mock_db_session.close.assert_called_once()
