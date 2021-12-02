from datetime import datetime, timezone


def midnight():
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
