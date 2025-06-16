class AtomicAPIError(Exception):
    """Base exception class for all atomic-sdk errors."""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(AtomicAPIError):
    """Raised for authentication failures (e.g., HTTP 401, 403)."""
    def __init__(self, message="Authentication failed. Please check your API key.", status_code=None):
        super().__init__(message, status_code)


class InvalidRequestError(AtomicAPIError):
    """Raised for client-side errors (e.g., HTTP 400, 422)."""
    def __init__(self, message="Invalid request.", status_code=None):
        super().__init__(message, status_code)


class NotFoundError(AtomicAPIError):
    """Raised when a resource is not found (e.g., HTTP 404)."""
    def __init__(self, message="The requested resource was not found.", status_code=404):
        super().__init__(message, status_code)


class ServerError(AtomicAPIError):
    """Raised for server-side errors (e.g., HTTP 5xx)."""
    def __init__(self, message="An unexpected server error occurred.", status_code=None):
        super().__init__(message, status_code)
