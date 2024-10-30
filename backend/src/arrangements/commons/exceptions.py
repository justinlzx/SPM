from .enums import Action, ApprovalStatus


class ArrangementNotFoundException(Exception):
    def __init__(self, arrangement_id: int):
        self.message = f"Arrangement with ID {arrangement_id} not found"
        super().__init__(self.message)


class ArrangementActionNotAllowedException(Exception):
    def __init__(self, current_approval_status: ApprovalStatus, action: Action):
        self.message = f"Action {action} not allowed for current status {current_approval_status}"
        super().__init__(self.message)


class S3UploadFailedException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
