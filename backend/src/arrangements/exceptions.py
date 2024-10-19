class ArrangementNotFoundException(Exception):
    def __init__(self, arrangement_id: int):
        self.message = f"Arrangement with ID {arrangement_id} not found"
        super().__init__(self.message)


class ArrangementActionNotAllowedException(Exception):
    def __init__(self, arrangement_id: int, action: str):
        self.message = "Default message"
        if action == "approve" or action == "reject":
            self.message = f"Arrangement with ID {arrangement_id} is not in pending status"
        super().__init__(self.message)
