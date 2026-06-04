import pytest

from apps.auth_service.app.domain.entities import RegisteredUser
from apps.auth_service.app.domain.value_objects import EmailAddress, FullName, Username


@pytest.mark.parametrize(
    ("value", "expected_message"),
    [
        ("ab", "Username must be at least 3 characters long"),
        ("x" * 81, "Username must be 80 characters or fewer"),
    ],
)
def test_username_rejects_invalid_values(value: str, expected_message: str) -> None:
    with pytest.raises(ValueError, match=expected_message):
        Username(value)


@pytest.mark.parametrize(
    ("value", "expected_message"),
    [
        ("invalid-email", "Invalid email address"),
        ("@example.com", "Invalid email address"),
        ("user@", "Invalid email address"),
    ],
)
def test_email_address_rejects_invalid_values(
    value: str,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError, match=expected_message):
        EmailAddress(value)


@pytest.mark.parametrize(
    ("first_name", "last_name", "expected_message"),
    [
        ("", "Doe", "First name cannot be empty"),
        ("John", "", "Last name cannot be empty"),
    ],
)
def test_full_name_rejects_blank_parts(
    first_name: str,
    last_name: str,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError, match=expected_message):
        FullName(first_name=first_name, last_name=last_name)


def test_registered_user_requires_user_id() -> None:
    with pytest.raises(ValueError, match="User id cannot be empty"):
        RegisteredUser(
            user_id=" ",
            username="john.doe",
            email="john@example.com",
            full_name=("John", "Doe"),
        )
