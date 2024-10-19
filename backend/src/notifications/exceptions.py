class EmailNotificationException(Exception):
    def __init__(self, emails: list[str]):
        self.message = f"Failed to send emails to {', '.join(emails)}"
        super().__init__(self.message)
