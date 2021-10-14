import time

from api.config import timer_duration


class WaitForTimer:
    def run(self, client, case):
        time.sleep(timer_duration)
