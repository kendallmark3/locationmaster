"""Deterministic local tools used by the capability workflow."""

from datetime import datetime, timezone


def get_application_status() -> dict:
    """Return a snapshot of application status without any external calls."""
    return {
        "application": "locationmaster",
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }
