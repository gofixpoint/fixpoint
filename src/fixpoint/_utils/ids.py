"""Module for common code among resource identifiers."""

import uuid


def make_resource_uuid(resource_acronym: str) -> str:
    """Make a UUID prefixed with a resource type acronym."""
    return "".join([resource_acronym, "-", str(uuid.uuid4())])
