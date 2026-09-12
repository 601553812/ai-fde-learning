"""Read and validate one public, non-secret environment setting."""

import os
from dataclasses import dataclass

from fastapi import HTTPException

ENV_NAME = "AI_FDE_MAX_TEXT_LENGTH"
CONFIG_ERROR_MESSAGE = "AI_FDE_MAX_TEXT_LENGTH must be an integer from 1 to 10000"


@dataclass(frozen=True)
class Settings:
    max_text_length: int = 2000


class ConfigurationError(ValueError):
    """An invalid value supplied by the server operator."""


def load_settings() -> Settings:
    raw = os.getenv(ENV_NAME,2000)
    length = 0
    try:
        length = int(raw)
    except ValueError:
        raise ConfigurationError(CONFIG_ERROR_MESSAGE)
    if 1 <= length <= 10000:
        return Settings(max_text_length=length)
    else:
        raise ConfigurationError(CONFIG_ERROR_MESSAGE)



def get_settings() -> Settings:
    """Provided adapter: turn only known configuration errors into HTTP 503."""
    try:
        return load_settings()
    except ConfigurationError as error:
        raise HTTPException(
            status_code=503,
            detail={"code": "CONFIGURATION_INVALID", "message": "Server configuration is invalid"},
        ) from error
