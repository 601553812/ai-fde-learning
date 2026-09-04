"""Fetch requirement data from a JSON HTTP API."""

from __future__ import annotations

import requests
from pydantic import ValidationError

from day06.models import RequirementData


class RequirementApiError(RuntimeError):
    """Public error raised when remote requirement data cannot be loaded."""


def fetch_requirement(
    url: str,
    timeout_seconds: float = 5.0,
) -> RequirementData:
    """Fetch, decode, and validate requirement data from an HTTP endpoint."""
    try:
        response = requests.get(url, timeout=timeout_seconds)
        response.raise_for_status()
        response_json = response.json()
        return RequirementData.model_validate(response_json)
    except (requests.RequestException,ValidationError) as e:
        raise RequirementApiError("default error message") from e
