from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError
from src.arrangements.commons.enums import (
    Action,
    ApprovalStatus,
    RecurringFrequencyUnit,
    WfhType,
)
from src.arrangements.commons.schemas import (
    ArrangementFilters,
    ArrangementLogResponse,
    ArrangementResponse,
    CreateArrangementRequest,
    UpdateArrangementRequest,
)

singapore_timezone = ZoneInfo("Asia/Singapore")


@pytest.fixture
def arrangement_response():
    return ArrangementResponse(
        arrangement_id=1,
        update_datetime=datetime(2024, 9, 10, 0, 0),
        requester_staff_id=1,
        wfh_date=datetime(2024, 10, 10).date(),
        wfh_type=WfhType.FULL,
        current_approval_status=ApprovalStatus.PENDING_APPROVAL,
        approving_officer=2,
        delegate_approving_officer=3,
        reason_description="Waiting for approval",
        batch_id=1,
        latest_log_id=1,
        supporting_doc_1="https://example.com/doc1",
        supporting_doc_2="https://example.com/doc2",
        supporting_doc_3="https://example.com/doc3",
        status_reason="Manager approved",
    )


@pytest.fixture
def arrangement_log_response():
    return ArrangementLogResponse(
        log_id=1,
        update_datetime=datetime(2024, 9, 10, 0, 0),
        arrangement_id=1,
        requester_staff_id=1,
        wfh_date=datetime(2024, 10, 12).date(),
        wfh_type=WfhType.FULL,
        action=Action.APPROVE,
        previous_approval_status=ApprovalStatus.PENDING_APPROVAL,
        updated_approval_status=ApprovalStatus.APPROVED,
        approving_officer=2,
        reason_description="Manager approved WFH",
        batch_id=1,
        supporting_doc_1="https://example.com/doc1",
        supporting_doc_2="https://example.com/doc2",
        supporting_doc_3="https://example.com/doc3",
        status_reason="Manager approved",
    )


class TestArrangementFilters:
    # Test ArrangementFilters schema with valid data
    def test_valid(self):
        filters = ArrangementFilters(
            current_approval_status=[ApprovalStatus.PENDING_APPROVAL, ApprovalStatus.APPROVED],
            name="John Doe",
            wfh_type=[WfhType.FULL],
            start_date=datetime(2024, 10, 10).date(),
            end_date=datetime(2024, 10, 12).date(),
            reason="Need to work from home",
            group_by_date=True,
        )

        assert filters.current_approval_status == [
            ApprovalStatus.PENDING_APPROVAL,
            ApprovalStatus.APPROVED,
        ]
        assert filters.name == "John Doe"
        assert filters.wfh_type == [WfhType.FULL]
        assert filters.start_date == datetime(2024, 10, 10).date()
        assert filters.end_date == datetime(2024, 10, 12).date()
        assert filters.reason == "Need to work from home"
        assert filters.group_by_date is True

    @pytest.mark.parametrize(
        ("current_approval_status", "wfh_type"),
        [
            [None, ["full"]],
            [["pending approval", "approved"], None],
        ],
    )
    def test_parse_string_to_enum(self, current_approval_status, wfh_type):
        filters = ArrangementFilters(
            current_approval_status=current_approval_status,
            wfh_type=wfh_type,
        )  # type: ignore

        if current_approval_status:
            assert filters.current_approval_status == [
                ApprovalStatus.PENDING_APPROVAL,
                ApprovalStatus.APPROVED,
            ]
        if wfh_type:
            assert filters.wfh_type == [WfhType.FULL]

    def test_parse_string_to_date(self):
        filters = ArrangementFilters(
            start_date="2024-10-10",
            end_date="2024-10-12",
        )  # type: ignore
        assert filters.start_date == datetime(2024, 10, 10).date()
        assert filters.end_date == datetime(2024, 10, 12).date()


class TestCreateArrangementRequest:
    # Test ArrangementCreate schema with valid data
    @pytest.mark.parametrize(
        (
            "is_recurring",
            "recurring_frequency_number",
            "recurring_frequency_unit",
            "recurring_occurrences",
        ),
        [
            [False, None, None, None],
            [True, 1, RecurringFrequencyUnit.WEEKLY, 3],
        ],
    )
    def test_valid(
        self,
        is_recurring,
        recurring_frequency_number,
        recurring_frequency_unit,
        recurring_occurrences,
    ):
        arrangement = CreateArrangementRequest(
            requester_staff_id=1,
            wfh_date=datetime.strptime("2099-12-31", "%Y-%m-%d").date(),
            wfh_type=WfhType.FULL,
            is_recurring=is_recurring,
            recurring_frequency_number=recurring_frequency_number,
            recurring_frequency_unit=recurring_frequency_unit,
            recurring_occurrences=recurring_occurrences,
            reason_description="Need to work from home",
        )
        assert arrangement.requester_staff_id == 1
        assert arrangement.wfh_date == datetime.strptime("2099-12-31", "%Y-%m-%d").date()
        assert arrangement.wfh_type == WfhType.FULL
        assert arrangement.reason_description == "Need to work from home"
        assert arrangement.is_recurring is is_recurring
        assert arrangement.recurring_frequency_number == recurring_frequency_number
        assert arrangement.recurring_frequency_unit == recurring_frequency_unit
        assert arrangement.recurring_occurrences == recurring_occurrences

    @pytest.mark.parametrize(
        "field",
        [
            "wfh_type",
            "recurring_frequency_unit",
        ],
    )
    def test_parse_string_to_enum(self, field):
        CreateArrangementRequest(
            requester_staff_id=1,
            wfh_date=datetime(2099, 12, 31).date(),
            wfh_type="full" if field != "wfh_type" else WfhType.FULL,  # type: ignore
            is_recurring=False,
            recurring_frequency_number=None,
            recurring_frequency_unit=(
                "week" if field != "recurring_frequency_unit" else RecurringFrequencyUnit.WEEKLY
            ),  # type: ignore
            recurring_occurrences=None,
            reason_description="Need to work from home",
        )

    def test_parse_string_to_date_datetime(self):
        CreateArrangementRequest(
            requester_staff_id=1,
            wfh_date="2099-12-31",
            wfh_type=WfhType.FULL,
            is_recurring=False,
        )  # type: ignore

    def test_parse_string_to_int(self):
        CreateArrangementRequest(
            requester_staff_id="1",
            wfh_date=datetime(2099, 12, 31).date(),
            wfh_type=WfhType.FULL,
            is_recurring=False,
        )  # type: ignore

    @pytest.mark.parametrize(
        "field",
        [
            "requester_staff_id",
            "wfh_date",
            "wfh_type",
            "is_recurring",
        ],
    )
    def test_missing_required_fields(self, field):
        with pytest.raises(ValidationError):
            CreateArrangementRequest(
                requester_staff_id=1 if field != "requester_staff_id" else None,
                wfh_date=(
                    datetime.strptime("2099-10-10", "%Y-%m-%d").date()
                    if field != "wfh_date"
                    else None
                ),
                wfh_type=WfhType.FULL if field != "wfh_type" else None,
                is_recurring=False if field != "is_recurring" else None,
            )  # type: ignore

    @pytest.mark.parametrize(
        "field",
        [
            "recurring_frequency_number",
            "recurring_frequency_unit",
            "recurring_occurrences",
        ],
    )
    def test_missing_recurring_fields(self, field):
        with pytest.raises(ValueError):
            CreateArrangementRequest(
                requester_staff_id=1,
                wfh_date=datetime.strptime("2099-12-31", "%Y-%m-%d").date(),
                wfh_type=WfhType.FULL,
                is_recurring=True,
                recurring_frequency_number=1 if field != "recurring_frequency_number" else None,
                recurring_frequency_unit=(
                    RecurringFrequencyUnit.WEEKLY if field != "recurring_frequency_unit" else None
                ),
                recurring_occurrences=3 if field != "recurring_occurrences" else None,
            )  # type: ignore

    @pytest.mark.parametrize(
        "field",
        [
            "recurring_frequency_number",
            "recurring_occurrences",
        ],
    )
    def test_zero_value_recurring_fields(self, field):
        with pytest.raises(ValueError):
            CreateArrangementRequest(
                requester_staff_id=1,
                wfh_date=datetime.strptime("2099-12-31", "%Y-%m-%d").date(),
                wfh_type=WfhType.FULL,
                is_recurring=True,
                recurring_frequency_number=1 if field != "recurring_frequency_number" else 0,
                recurring_frequency_unit=RecurringFrequencyUnit.WEEKLY,
                recurring_occurrences=3 if field != "recurring_occurrences" else 0,
            )  # type: ignore

    def test_wfh_date_less_than_24h(self):
        wfh_date = datetime.now(singapore_timezone).date() + timedelta(hours=23)

        with pytest.raises(ValueError):
            CreateArrangementRequest(
                requester_staff_id=1,
                wfh_date=wfh_date,
                wfh_type=WfhType.FULL,
                is_recurring=False,
            )  # type: ignore


class TestUpdateArrangementRequest:
    # Test ArrangementUpdate schema with valid data
    def test_valid(self):
        update = UpdateArrangementRequest(
            action=Action.APPROVE,
            approving_officer=2,
            status_reason="Manager approved",
        )
        assert update.action == Action.APPROVE
        assert update.approving_officer == 2
        assert update.status_reason == "Manager approved"

    @pytest.mark.parametrize(
        "field",
        [
            "action",
            "approving_officer",
        ],
    )
    def test_missing_required_field(self, field):
        with pytest.raises(ValidationError):
            UpdateArrangementRequest(
                action=Action.APPROVE if field != "action" else None,
                approving_officer=2 if field != "approving_officer" else None,
            )  # type: ignore

    def test_parse_string_to_enum(self):
        UpdateArrangementRequest(
            action="approve",  # type: ignore
            approving_officer=2,
            status_reason="Manager approved",
        )


class TestArrangementResponse:
    # Test ArrangementResponse schema with valid data
    def test_valid(self, arrangement_response):
        response = arrangement_response
        assert response.arrangement_id == 1
        assert response.update_datetime == datetime(2024, 9, 10, 0, 0)
        assert response.requester_staff_id == 1
        assert response.wfh_date == datetime(2024, 10, 10).date()
        assert response.wfh_type == WfhType.FULL
        assert response.current_approval_status == ApprovalStatus.PENDING_APPROVAL
        assert response.approving_officer == 2
        assert response.delegate_approving_officer == 3
        assert response.reason_description == "Waiting for approval"
        assert response.batch_id == 1
        assert response.latest_log_id == 1
        assert response.supporting_doc_1 == "https://example.com/doc1"
        assert response.supporting_doc_2 == "https://example.com/doc2"
        assert response.supporting_doc_3 == "https://example.com/doc3"
        assert response.status_reason == "Manager approved"

    def test_field_serializers(self, arrangement_response):
        response = arrangement_response
        json_data = response.model_dump()
        assert json_data["wfh_date"] == "2024-10-10"
        assert json_data["update_datetime"] == "2024-09-10T00:00:00"
        assert json_data["current_approval_status"] == "pending approval"
        assert json_data["wfh_type"] == "full"


class TestArrangementLogResponse:
    # Test ArrangementLogResponse schema with valid data
    def test_valid(self, arrangement_log_response):
        assert arrangement_log_response.log_id == 1
        assert arrangement_log_response.update_datetime == datetime(2024, 9, 10, 0, 0)
        assert arrangement_log_response.arrangement_id == 1
        assert arrangement_log_response.requester_staff_id == 1
        assert arrangement_log_response.wfh_date == datetime(2024, 10, 12).date()
        assert arrangement_log_response.wfh_type == WfhType.FULL
        assert arrangement_log_response.action == Action.APPROVE
        assert arrangement_log_response.previous_approval_status == ApprovalStatus.PENDING_APPROVAL
        assert arrangement_log_response.updated_approval_status == ApprovalStatus.APPROVED
        assert arrangement_log_response.approving_officer == 2
        assert arrangement_log_response.reason_description == "Manager approved WFH"
        assert arrangement_log_response.batch_id == 1
        assert arrangement_log_response.supporting_doc_1 == "https://example.com/doc1"
        assert arrangement_log_response.supporting_doc_2 == "https://example.com/doc2"
        assert arrangement_log_response.supporting_doc_3 == "https://example.com/doc3"
        assert arrangement_log_response.status_reason == "Manager approved"

    @pytest.mark.parametrize(
        "field",
        [
            "log_id",
            "update_datetime",
            "arrangement_id",
            "requester_staff_id",
            "wfh_date",
            "wfh_type",
            "action",
            "previous_approval_status",
            "updated_approval_status",
            "approving_officer",
            "status_reason",
        ],
    )
    def test_missing_required_fields(self, field):
        with pytest.raises(ValidationError):
            ArrangementLogResponse(
                log_id=1 if field != "log_id" else None,
                update_datetime=datetime(2024, 9, 10, 0, 0) if field != "update_datetime" else None,
                arrangement_id=1 if field != "arrangement_id" else None,
                requester_staff_id=1 if field != "requester_staff_id" else None,
                wfh_date=datetime(2024, 10, 12).date() if field != "wfh_date" else None,
                wfh_type=WfhType.FULL if field != "wfh_type" else None,
                action=Action.APPROVE if field != "action" else None,
                previous_approval_status=(
                    ApprovalStatus.PENDING_APPROVAL if field != "previous_approval_status" else None
                ),
                updated_approval_status=(
                    ApprovalStatus.APPROVED if field != "updated_approval_status" else None
                ),
                approving_officer=2 if field != "approving_officer" else None,
            )  # type: ignore

    def test_model_dump(self, arrangement_log_response):
        response = arrangement_log_response
        json_data = response.model_dump()
        assert json_data["wfh_date"].isoformat() == "2024-10-12"
        assert json_data["update_datetime"].isoformat() == "2024-09-10T00:00:00"
        assert json_data["action"].value == "approve"
        assert json_data["previous_approval_status"].value == "pending approval"
        assert json_data["updated_approval_status"].value == "approved"
        assert json_data["wfh_type"].value == "full"
