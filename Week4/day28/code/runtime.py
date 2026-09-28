"""Select offline or real model dependencies for each HTTP request."""

import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal


from fastapi import HTTPException

from .fakes import RecordingSleeper, SequenceGateway
from .gemini_gateway import GeminiGateway


@dataclass
class BatchRuntime:
    gateway_factory: Callable
    sleeper: Callable


def local_gateway(task_id: str):
    return SequenceGateway([f"模擬結果：{task_id}"])

def live_gateway(_task_id: str) -> GeminiGateway:
    return GeminiGateway()


def get_runtime(mode: Literal["simulated", "live"] = "simulated") -> BatchRuntime:
    if mode == "simulated":
        return BatchRuntime(local_gateway, RecordingSleeper())
    if mode == "live":
        google_api_key = os.getenv("GOOGLE_API_KEY")
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if google_api_key :
            if google_api_key.strip():
                return BatchRuntime(live_gateway, time.sleep)
        if gemini_api_key:
            if gemini_api_key.strip():
                return BatchRuntime(live_gateway, time.sleep)
            else:
                raise HTTPException(status_code=503, detail={"code": "MODEL_NOT_CONFIGURED", "message": "Gemini API key is not configured"})
        else:
            raise HTTPException(status_code=503, detail={"code": "MODEL_NOT_CONFIGURED", "message": "Gemini API key is not configured"})
    return BatchRuntime(local_gateway, RecordingSleeper())