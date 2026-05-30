"""Auth Service domain exceptions."""


class UserAlreadyExistsError(Exception):
    """Raised when a registration email is already used."""


class UserNotFoundError(Exception):
    """Raised when a user does not exist."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""
