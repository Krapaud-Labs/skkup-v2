"""Business civil-time helpers shared by authentication and daily rewards."""

import os
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo


def business_timezone() -> ZoneInfo:
    return ZoneInfo(os.environ.get("TZ", "Europe/Paris"))


def business_day(value: datetime) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(business_timezone()).date()
