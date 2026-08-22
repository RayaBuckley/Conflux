"""Small shared enums that avoid cycles between actions and delegation values."""

from enum import StrEnum


class ArgumentRole(StrEnum):
    """Classifies the role an action argument plays in authority evaluation."""

    CONTENT = "content"
    RESOURCE = "resource"
    RECIPIENT = "recipient"
    DESTINATION = "destination"
    VALUE = "value"
    CREDENTIAL_REFERENCE = "credential_reference"


__all__ = ["ArgumentRole"]
