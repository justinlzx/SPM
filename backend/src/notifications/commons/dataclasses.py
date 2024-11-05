from dataclasses import dataclass
from typing import List

from ...arrangements.commons.dataclasses import ArrangementResponse
from ...arrangements.commons.enums import Action, ApprovalStatus
from ...employees.models import Employee


@dataclass
class ArrangementNotificationConfig:
    employee: Employee
    arrangements: List[ArrangementResponse]
    action: Action
    current_approval_status: ApprovalStatus
    manager: Employee


@dataclass
class DelegateNotificationConfig:
    delegator: Employee
    delegatee: Employee
    action: str
