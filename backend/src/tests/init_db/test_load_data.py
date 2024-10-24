import os
from datetime import datetime

import pandas as pd
from src.init_db.load_data import (
    load_auth_data_from_csv,
    load_employee_data_from_csv,
    load_latest_arrangement_data_from_csv,
)

from ...auth.utils import hash_password

# -------------------------------- Employee Data Tests --------------------------------


def test_load_employee_data_from_csv(mock_db_session):
    load_employee_data_from_csv("src/tests/init_db/test_employee.csv")
    assert mock_db_session.add.call_count == 554
    df = pd.read_csv("src/tests/init_db/test_employee.csv")
    actual_employees = [call[0][0] for call in mock_db_session.add.call_args_list]

    for i, row in df.iterrows():
        # Compare each attribute in actual_employees
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


def test_load_employee_data_file_not_found(mock_db_session, capsys):
    load_employee_data_from_csv("src/tests/init_db/non_existent_file.csv")
    captured = capsys.readouterr()
    assert (
        "Error: The file 'src/tests/init_db/non_existent_file.csv' was not found." in captured.out
    )


def test_load_employee_data_empty_file(mock_db_session, mocker, capsys):
    # Mock pandas to simulate an empty CSV file
    mocker.patch("pandas.read_csv", side_effect=pd.errors.EmptyDataError)
    load_employee_data_from_csv("src/tests/init_db/empty.csv")
    captured = capsys.readouterr()
    assert "Error: The file 'src/tests/init_db/empty.csv' is empty." in captured.out


def test_load_employee_data_from_csv_exception(mock_db_session, mocker, capsys):
    # Mock the Employee model to raise an exception during instantiation
    mocker.patch(
        "src.init_db.load_data.Employee", side_effect=Exception("Test Exception for Employee")
    )

    # Call the function with a mock CSV path
    load_employee_data_from_csv("src/tests/init_db/test_employee.csv")

    # Capture the stdout to check for the error message
    captured = capsys.readouterr()
    # Assert that the exception message is logged correctly
    assert (
        "An error occurred while loading employee data: Test Exception for Employee" in captured.out
    )

    # Ensure rollback is called due to exception
    mock_db_session.rollback.assert_called_once()
    # Ensure commit is not called
    mock_db_session.commit.assert_not_called()
    # Ensure the session is closed after exception
    mock_db_session.close.assert_called_once()


def test_load_employee_data_generic_exception(mock_db_session, mocker, capsys):
    mocker.patch("pandas.read_csv", side_effect=Exception("Generic read exception"))

    load_employee_data_from_csv("src/tests/init_db/test_employee.csv")
    captured = capsys.readouterr()
    assert (
        "An unexpected error occurred while reading 'src/tests/init_db/test_employee.csv': Generic read exception"
        in captured.out
    )


# -------------------------------- Auth Data Tests --------------------------------


def test_load_auth_data_from_csv(mock_db_session):
    # Call the function to load auth data from the CSV
    load_auth_data_from_csv("src/tests/init_db/test_auth.csv")

    # Check that the correct number of records have been added to the database
    assert mock_db_session.add.call_count == 554

    # Read the CSV file to verify data
    df = pd.read_csv("src/tests/init_db/test_auth.csv")
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


def test_load_auth_data_file_not_found(mock_db_session, capsys):
    load_auth_data_from_csv("src/tests/init_db/non_existent_file.csv")
    captured = capsys.readouterr()
    assert (
        "Error: The file 'src/tests/init_db/non_existent_file.csv' was not found." in captured.out
    )


def test_load_auth_data_empty_file(mock_db_session, mocker, capsys):
    # Mock pandas to simulate an empty CSV file
    mocker.patch("pandas.read_csv", side_effect=pd.errors.EmptyDataError)
    load_auth_data_from_csv("src/tests/init_db/empty.csv")
    captured = capsys.readouterr()
    assert "Error: The file 'src/tests/init_db/empty.csv' is empty." in captured.out


def test_load_auth_data_from_csv_exception(mock_db_session, mocker, capsys):
    # Mock the Auth model to raise an exception during instantiation
    mocker.patch("src.init_db.load_data.Auth", side_effect=Exception("Test Exception for Auth"))

    # Call the function with a mock CSV path
    load_auth_data_from_csv("src/tests/init_db/test_auth.csv")

    # Capture the stdout to check for the error message
    captured = capsys.readouterr()
    # Assert that the exception message is logged correctly
    assert "An error occurred while loading auth data: Test Exception for Auth" in captured.out

    # Ensure rollback is called due to exception
    mock_db_session.rollback.assert_called_once()
    # Ensure commit is not called
    mock_db_session.commit.assert_not_called()
    # Ensure the session is closed after exception
    mock_db_session.close.assert_called_once()


def test_load_auth_data_generic_exception(mock_db_session, mocker, capsys):
    mocker.patch("pandas.read_csv", side_effect=Exception("Generic read exception"))

    load_auth_data_from_csv("src/tests/init_db/test_auth.csv")
    captured = capsys.readouterr()
    assert (
        "An unexpected error occurred while reading 'src/tests/init_db/test_auth.csv': Generic read exception"
        in captured.out
    )


# -------------------------------- Arrangement Data Tests --------------------------------


def test_load_latest_arrangement_data_from_csv(mock_db_session, mocker):
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
    load_latest_arrangement_data_from_csv(csv_path)

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
                int(row["approving_officer"]) if pd.notna(row["approving_officer"]) else None
            ),
            reason_description=row["reason_description"],
            batch_id=int(row["batch_id"]) if pd.notna(row["batch_id"]) else None,
        )

    # Verify that commit and close were called on the session
    mock_db_session.commit.assert_called_once()
    mock_db_session.close.assert_called_once()


def test_load_arrangement_data_file_not_found(mock_db_session, capsys):
    load_latest_arrangement_data_from_csv("src/tests/init_db/non_existent_file.csv")
    captured = capsys.readouterr()
    assert (
        "Error: The file 'src/tests/init_db/non_existent_file.csv' was not found." in captured.out
    )


def test_load_arrangement_data_empty_file(mock_db_session, mocker, capsys):
    # Mock pandas to simulate an empty CSV file
    mocker.patch("pandas.read_csv", side_effect=pd.errors.EmptyDataError)
    load_latest_arrangement_data_from_csv("src/tests/init_db/empty.csv")
    captured = capsys.readouterr()
    assert "Error: The file 'src/tests/init_db/empty.csv' is empty." in captured.out


def test_load_arrangement_data_key_error(mock_db_session, mocker, capsys):
    # Mock the ArrangementLog model to raise a KeyError during instantiation
    mocker.patch("src.init_db.load_data.ArrangementLog", side_effect=KeyError("Test KeyError"))

    load_latest_arrangement_data_from_csv("src/tests/init_db/test_arrangement.csv")
    captured = capsys.readouterr()
    assert "Missing expected column in CSV: 'Test KeyError'" in captured.out


def test_load_arrangement_data_value_error(mock_db_session, mocker, capsys):
    # Mock the ArrangementLog model to raise a ValueError during instantiation
    mocker.patch("src.init_db.load_data.ArrangementLog", side_effect=ValueError("Test ValueError"))

    load_latest_arrangement_data_from_csv("src/tests/init_db/test_arrangement.csv")
    captured = capsys.readouterr()
    assert "Data conversion error: Test ValueError" in captured.out


def test_load_latest_arrangement_data_from_csv_exception(mock_db_session, mocker, capsys):
    # Mock pandas.read_csv to raise an exception to trigger the rollback logic
    mocker.patch("pandas.read_csv", side_effect=Exception("Test Exception"))

    # Call the function with a mock CSV path
    try:
        load_latest_arrangement_data_from_csv("src/tests/init_db/test_arrangement.csv")
    except Exception:
        # This is expected because we are forcing an exception
        pass

    # Capture the stdout to check for the error message
    captured = capsys.readouterr()
    # Assert the correct message is printed
    assert "An unexpected error occurred: Test Exception" in captured.out

    # Ensure rollback is called due to exception
    mock_db_session.rollback.assert_called_once()
    # Ensure commit is not called
    mock_db_session.commit.assert_not_called()
    # Ensure the session is closed after exception
    mock_db_session.close.assert_called_once()


def test_load_arrangement_data_generic_exception(mock_db_session, mocker, capsys):
    # Mock pandas read_csv to raise a generic exception
    mocker.patch("pandas.read_csv", side_effect=Exception("Generic read exception"))

    # Call the function to trigger the exception
    load_latest_arrangement_data_from_csv("src/tests/init_db/test_arrangement.csv")

    # Capture the stdout and stderr
    captured = capsys.readouterr()

    # Assert the expected error message is present in the output
    assert (
        "An unexpected error occurred: Generic read exception" in captured.out
    ), f"Captured output: {captured.out}"


# Test when the arrangement data CSV is empty after reading
def test_load_arrangement_data_empty_dataframe(mock_db_session, mocker, capsys):
    # Mock pandas to return an empty DataFrame
    mocker.patch("pandas.read_csv", return_value=pd.DataFrame())

    load_latest_arrangement_data_from_csv("src/tests/init_db/empty.csv")
    captured = capsys.readouterr()
    assert "Error: The file 'src/tests/init_db/empty.csv' is empty." in captured.out

    # Ensure that commit and rollback are not called
    mock_db_session.commit.assert_not_called()
    mock_db_session.rollback.assert_not_called()
    mock_db_session.close.assert_called_once()


# Test when an exception is raised while processing a row in the arrangement data CSV
def test_load_arrangement_data_row_exception(mock_db_session, mocker, capsys):
    # Mock the csv.DictReader to return valid rows
    # mock_csv_reader = mocker.patch(
    #     "csv.DictReader",
    #     return_value=[
    #         {
    #             "update_datetime": "2024-10-05 23:00:00",
    #             "wfh_date": "2024-10-05",
    #             "wfh_type": "WFH",
    #             "reason_description": "Reason",
    #             "requester_staff_id": "1",
    #             "approval_status": "approved",
    #             "approving_officer": "2",
    #             "batch_id": "100",
    #         }
    #     ],
    # )

    # Mock ArrangementLog to raise a generic exception during instantiation
    mocker.patch(
        "src.init_db.load_data.ArrangementLog", side_effect=Exception("Test Row Exception")
    )

    # Call the function with a mock CSV path
    load_latest_arrangement_data_from_csv("src/tests/init_db/test_arrangement.csv")
    captured = capsys.readouterr()

    # Assert the correct message is printed when an exception occurs in row processing
    assert "An unexpected error occurred while processing row: Test Row Exception" in captured.out

    # Ensure that the database session is closed properly
    mock_db_session.close.assert_called_once()
