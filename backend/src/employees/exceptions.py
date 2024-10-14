class EmployeeNotFoundException(Exception):
    def __init__(self):
        super().__init__("Employee not found")


class ManagerWithIDNotFoundException(Exception):
    def __init__(self, manager_id: int):
        self.manager_id = manager_id
        super().__init__(f"Manager with ID {manager_id} not found")


class ManagerNotFoundException(Exception):
    def __init__(self):
        super().__init__("Manager not found")
