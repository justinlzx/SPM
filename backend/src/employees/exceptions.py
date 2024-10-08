class EmployeeNotFoundException(Exception):
    def __init__(self):
        super().__init__("Employee not found")


class ManagerNotFoundException(Exception):
    def __init__(self):
        super().__init__("Manager not found")
