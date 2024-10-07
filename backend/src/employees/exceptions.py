class EmployeeNotFound(Exception):
    def __init__(self):
        super().__init__("Employee not found")


class ManagerNotFound(Exception):
    def __init__(self):
        super().__init__("Manager not found")
