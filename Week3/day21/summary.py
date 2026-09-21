"""Day21: summarize completed reports without issuing more requests."""

from .retry_service import RetryResult


def summarize(reports: list[RetryResult]) -> dict[str, int]:
    requests = len(reports)
    succeeded = 0
    failed = 0
    total_attempts = 0
    for report in reports:
        if report.result.ok:
            succeeded += 1
        else:
            failed += 1
        total_attempts = total_attempts + report.attempts
    total_retries = total_attempts - requests
    return {
        "requests": requests,
        "succeeded": succeeded,
        "failed": failed,
        "attempts": total_attempts,
        "retries": total_retries,
    }