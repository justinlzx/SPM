class InvalidEmailException(Exception):
    def __init__(self, email: int):
        self.message = f"Email '{email}' is not in the correct format"
        super().__init__(self.message)
