import datetime
import logging
import time

from api.config import timer_duration

logger = logging.getLogger(__name__)


def wait_for(fn, timeout, sleep_time):
    timeout_at = datetime.datetime.now() + datetime.timedelta(seconds=timeout)

    while True:
        if datetime.datetime.now() > timeout_at:
            return False

        res = fn()
        if res:
            return res

        time.sleep(sleep_time)


class WaitForTimer:
    def run(self, client, case):
        logger.info("Waiting for timer...")
        time.sleep(timer_duration)
