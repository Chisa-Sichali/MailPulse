class MailPulseError(Exception):
    """Base application error."""

    def __init__(self, message: str, *, code: str = "internal_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(MailPulseError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="not_found")


class ConflictError(MailPulseError):
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, code="conflict")


class AuthenticationError(MailPulseError):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, code="authentication_error")


class AuthorizationError(MailPulseError):
    def __init__(self, message: str = "Not authorized") -> None:
        super().__init__(message, code="authorization_error")


class ValidationError(MailPulseError):
    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message, code="validation_error")
