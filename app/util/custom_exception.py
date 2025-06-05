
class CustomException(Exception):
    def __init__(self, message, error_code:int):
        self.message = message
        self.error_code = error_code
        super().__init__(f"{message} (Error code: {error_code})")

