import pytest
from datetime import datetime
from pydantic import ValidationError
from src.arrangements.schemas import (
    ArrangementCreate,
    ArrangementCreateWithFile,
    ArrangementUpdate,
    ArrangementLog,
    ArrangementResponse,
)
from src.tests.test_utils import mock_db_session


# Test ArrangementCreate schema with valid data
def test_arrangement_create_valid():
    arrangement = ArrangementCreate(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="full",
        approving_officer=2,
        reason_description="Need to work from home",
    )
    assert arrangement.staff_id == 1
    assert arrangement.wfh_type == "full"
    assert arrangement.current_approval_status == "pending"
    assert isinstance(arrangement.update_datetime, datetime)


# Test ArrangementCreate with invalid data (missing staff_id)
def test_arrangement_create_missing_staff_id():
    with pytest.raises(ValidationError):
        ArrangementCreate(
            wfh_date="2024-10-10",
            wfh_type="full",
            approving_officer=2,
            reason_description="Need to work from home",
        )


# Test recurring field validation (valid case)
def test_arrangement_create_recurring_valid():
    arrangement = ArrangementCreate(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="am",
        approving_officer=2,
        reason_description="Recurring work from home",
        is_recurring=True,
        recurring_frequency_number=2,
        recurring_occurrences=4,
    )
    assert arrangement.is_recurring is True
    assert arrangement.recurring_frequency_number == 2
    assert arrangement.recurring_occurrences == 4


# Test recurring field validation (invalid case)
def test_arrangement_create_recurring_invalid():
    with pytest.raises(ValueError, match="must have a non-zero value"):
        ArrangementCreate(
            staff_id=1,
            wfh_date="2024-10-10",
            wfh_type="am",
            approving_officer=2,
            reason_description="Invalid recurring WFH",
            is_recurring=True,
            recurring_frequency_number=0,
            recurring_occurrences=0,
        )


# Test ArrangementCreateWithFile schema with valid data
def test_arrangement_create_with_file_valid():
    arrangement = ArrangementCreateWithFile(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="full",
        approving_officer=2,
        reason_description="Need to work from home",
        supporting_doc_1="https://example.com/doc1",
        supporting_doc_2="https://example.com/doc2",
    )
    assert arrangement.supporting_doc_1 == "https://example.com/doc1"
    assert arrangement.supporting_doc_2 == "https://example.com/doc2"


# Test ArrangementUpdate schema with valid data
def test_arrangement_update_valid():
    update = ArrangementUpdate(
        staff_id=1,
        wfh_date="2024-10-11",
        wfh_type="pm",
        action="approve",
        approving_officer=3,
        reason_description="Manager approved",
    )
    assert update.action == "approve"
    assert update.staff_id == 1
    assert update.wfh_type == "pm"


# Test ArrangementUpdate with invalid action
def test_arrangement_update_invalid_action():
    with pytest.raises(ValidationError):
        ArrangementUpdate(
            staff_id=1,
            wfh_date="2024-10-11",
            wfh_type="pm",
            action="invalid_action",  # Invalid action type
            approving_officer=3,
            reason_description="Invalid action type",
        )


# Test ArrangementLog schema with valid data
def test_arrangement_log_valid():
    log = ArrangementLog(
        arrangement_id=1,
        staff_id=1,
        wfh_date="2024-10-12",
        wfh_type="full",
        update_datetime=datetime.now(),
        approval_status="approved",
        reason_description="Manager approved WFH",
    )
    assert log.arrangement_id == 1
    assert log.approval_status == "approved"


# Test ArrangementResponse schema
def test_arrangement_response_valid():
    response = ArrangementResponse(
        arrangement_id=1,
        staff_id=1,
        wfh_date="2024-10-13",
        wfh_type="am",
        approval_status="pending",
        approving_officer=2,
        reason_description="Waiting for approval",
        update_datetime=datetime.now(),  # Provide this required field
    )
    assert response.arrangement_id == 1
    assert response.approval_status == "pending"
    assert response.reason_description == "Waiting for approval"
    assert isinstance(response.update_datetime, datetime)


def test_arrangement_create_model_dump():
    arrangement = ArrangementCreate(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="full",
        approving_officer=2,
        reason_description="Need to work from home",
    )

    # Call the custom model_dump method
    data = arrangement.model_dump()

    # Ensure fields added manually in custom model_dump are included
    assert "update_datetime" in data
    assert "current_approval_status" in data
    assert data["update_datetime"] == arrangement.update_datetime
    assert data["current_approval_status"] == arrangement.current_approval_status

    # Call the superclass method directly to see what would be excluded by default
    base_data = super(ArrangementCreate, arrangement).model_dump()

    # These should be excluded in the base call and added in custom dump
    assert "update_datetime" not in base_data
    assert "current_approval_status" not in base_data


# Test validator when is_recurring is False (or not present)
def test_arrangement_create_non_recurring():
    arrangement = ArrangementCreate(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="am",
        approving_officer=2,
        reason_description="One-time WFH",
        is_recurring=False,  # Non-recurring case
    )

    # Ensure the validator doesn't raise any error and the instance is valid
    assert arrangement.is_recurring is False
    assert arrangement.recurring_frequency_number is None
    assert arrangement.recurring_occurrences is None


def test_arrangement_create_model_dump_includes_excluded_fields():
    arrangement = ArrangementCreate(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="full",
        approving_officer=2,
        reason_description="Need to work from home",
    )

    # Explicitly call model_dump to test all lines
    data = arrangement.model_dump()

    # Check that excluded fields were correctly included manually
    assert "update_datetime" in data
    assert "current_approval_status" in data
    assert data["update_datetime"] == arrangement.update_datetime
    assert data["current_approval_status"] == arrangement.current_approval_status

    # Ensure the fields not originally in the dump are absent from the super call
    base_data = super(ArrangementCreate, arrangement).model_dump()
    assert "update_datetime" not in base_data
    assert "current_approval_status" not in base_data


def test_arrangement_create_recurring_fields_valid():
    arrangement = ArrangementCreate(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="full",
        approving_officer=2,
        reason_description="Recurring work from home",
        is_recurring=True,
        recurring_frequency_number=1,  # Valid value
        recurring_occurrences=3,  # Valid value
    )
    # Validate that the recurring fields were correctly set
    assert arrangement.is_recurring is True
    assert arrangement.recurring_frequency_number == 1
    assert arrangement.recurring_occurrences == 3


def test_arrangement_create_recurring_fields_invalid_zero_values():
    # This should raise an error because is_recurring is True, but recurring fields are zero
    with pytest.raises(ValueError, match="must have a non-zero value"):
        ArrangementCreate(
            staff_id=1,
            wfh_date="2024-10-10",
            wfh_type="am",
            approving_officer=2,
            reason_description="Invalid recurring WFH",
            is_recurring=True,  # Test the case where is_recurring is True
            recurring_frequency_number=0,  # Invalid
            recurring_occurrences=0,  # Invalid
        )


def test_arrangement_create_non_recurring_fields_not_required():
    # Test case where is_recurring is explicitly False
    arrangement = ArrangementCreate(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="am",
        approving_officer=2,
        reason_description="One-time WFH",
        is_recurring=False,  # Non-recurring case
    )

    # Ensure that recurring fields are not required or set
    assert arrangement.is_recurring is False
    assert arrangement.recurring_frequency_number is None
    assert arrangement.recurring_occurrences is None


def test_arrangement_create_missing_is_recurring_defaults_to_false():
    arrangement = ArrangementCreate(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="full",
        approving_officer=2,
        reason_description="One-time WFH",
    )

    # By default, is_recurring should be False
    assert arrangement.is_recurring is False
    assert arrangement.recurring_frequency_number is None
    assert arrangement.recurring_occurrences is None


# Test recurring fields when they are None (invalid when is_recurring is True)
def test_arrangement_create_recurring_fields_none():
    with pytest.raises(ValueError, match="must have a non-zero value"):
        ArrangementCreate(
            staff_id=1,
            wfh_date="2024-10-10",
            wfh_type="am",
            approving_officer=2,
            reason_description="Invalid recurring WFH",
            is_recurring=True,  # Test case where is_recurring is True
            recurring_frequency_number=None,  # Invalid case
            recurring_occurrences=None,  # Invalid case
        )


def test_arrangement_create_with_file_model_dump():
    arrangement = ArrangementCreateWithFile(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="full",
        approving_officer=2,
        reason_description="Need to work from home",
        supporting_doc_1="https://example.com/doc1",
    )

    # Call the custom model_dump method
    data = arrangement.model_dump()

    # Ensure all expected fields are included
    assert "staff_id" in data
    assert "wfh_date" in data
    assert "wfh_type" in data
    assert "approving_officer" in data
    assert "reason_description" in data
    assert "supporting_doc_1" in data
    assert "update_datetime" in data
    assert "current_approval_status" in data

    # Check that the values are correct
    assert data["staff_id"] == 1
    assert data["wfh_date"] == "2024-10-10"
    assert data["wfh_type"] == "full"
    assert data["approving_officer"] == 2
    assert data["reason_description"] == "Need to work from home"
    assert data["supporting_doc_1"] == "https://example.com/doc1"
    assert isinstance(data["update_datetime"], datetime)
    assert data["current_approval_status"] == "pending"

    # Verify that supporting_doc_2 and supporting_doc_3 are None
    assert "supporting_doc_2" in data
    assert data["supporting_doc_2"] is None
    assert "supporting_doc_3" in data
    assert data["supporting_doc_3"] is None


def test_arrangement_create_with_file_model_dump_all_supporting_docs():
    arrangement = ArrangementCreateWithFile(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="full",
        approving_officer=2,
        reason_description="Need to work from home",
        supporting_doc_1="https://example.com/doc1",
        supporting_doc_2="https://example.com/doc2",
        supporting_doc_3="https://example.com/doc3",
    )

    data = arrangement.model_dump()

    # Check that all supporting doc fields are included and have correct values
    assert data["supporting_doc_1"] == "https://example.com/doc1"
    assert data["supporting_doc_2"] == "https://example.com/doc2"
    assert data["supporting_doc_3"] == "https://example.com/doc3"


def test_arrangement_create_recurring_fields_one_field_set():
    # Test when only recurring_frequency_number is set
    with pytest.raises(ValueError, match="must have a non-zero value"):
        ArrangementCreate(
            staff_id=1,
            wfh_date="2024-10-10",
            wfh_type="am",
            approving_officer=2,
            reason_description="Invalid recurring WFH",
            is_recurring=True,
            recurring_frequency_number=1,
            recurring_occurrences=None,
        )

    # Test when only recurring_occurrences is set
    with pytest.raises(ValueError, match="must have a non-zero value"):
        ArrangementCreate(
            staff_id=1,
            wfh_date="2024-10-10",
            wfh_type="am",
            approving_officer=2,
            reason_description="Invalid recurring WFH",
            is_recurring=True,
            recurring_frequency_number=None,
            recurring_occurrences=1,
        )


def test_arrangement_create_recurring_fields_zero_and_none():
    # Test when one field is zero and the other is None
    with pytest.raises(ValueError, match="must have a non-zero value"):
        ArrangementCreate(
            staff_id=1,
            wfh_date="2024-10-10",
            wfh_type="am",
            approving_officer=2,
            reason_description="Invalid recurring WFH",
            is_recurring=True,
            recurring_frequency_number=0,
            recurring_occurrences=None,
        )

    with pytest.raises(ValueError, match="must have a non-zero value"):
        ArrangementCreate(
            staff_id=1,
            wfh_date="2024-10-10",
            wfh_type="am",
            approving_officer=2,
            reason_description="Invalid recurring WFH",
            is_recurring=True,
            recurring_frequency_number=None,
            recurring_occurrences=0,
        )


def test_arrangement_create_non_recurring_fields():
    arrangement = ArrangementCreate(
        staff_id=1,
        wfh_date="2024-10-10",
        wfh_type="full",
        approving_officer=2,
        reason_description="Non-recurring work from home",
        is_recurring=False,
        recurring_frequency_number=None,
        recurring_occurrences=None,
    )

    # Validate that the recurring fields were correctly set
    assert arrangement.is_recurring is False
    assert arrangement.recurring_frequency_number is None
    assert arrangement.recurring_occurrences is None

    # Ensure that the validator doesn't raise any errors for non-recurring arrangements
    data = arrangement.model_dump()
    assert "recurring_frequency_number" in data
    assert data["recurring_frequency_number"] is None
    assert "recurring_occurrences" in data
    assert data["recurring_occurrences"] is None
