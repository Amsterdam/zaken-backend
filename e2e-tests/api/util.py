from datetime import datetime


def today():
    return (
        datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    )
