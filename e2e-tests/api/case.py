import logging

from api.config import async_sleep, async_timeout, validate_timeline
from api.timers import wait_for

logger = logging.getLogger("api")


class Case:
    """
    Technically different then workflow engine user-tasks. Create case is needed
    to trigger the first task in the workflow.
    """

    timeline = []

    def __init__(self, data, client, events):
        self.data = data
        self.client = client
        self.timeline = events

    def __str__(self):
        return f"<{self.__module__}.{self.__class__.__name__} id:{self.data['id']}>"

    def run_steps(self, *steps):
        steps = filter(lambda step: step is not None, steps)

        for step in steps:
            # Give Spiff some time to do async processing.
            # Keep retrying untill we have a timeout
            if hasattr(step, "is_ready") and not wait_for(
                lambda: step.is_ready(self.client, self), async_timeout, async_sleep
            ):
                raise Exception(f"Step ({step}) is not ready for case {self}.")

            step.run(self.client, self)

            # Append a timeline event for the step if expected
            if hasattr(step, "event") and step.event:
                self.timeline.append(step.event)

        def check_events():
            events = self.client.get_case_events(self.data["id"])
            expected_events = list(map(lambda event: event.type, self.timeline))
            found_events = list(map(lambda event: event["type"], events))

            logging.info(f"Finding events for case id {self.data['id']} ...")
            logging.info(f"Expected events:\n{expected_events}\nFound:\n{found_events}")

            return expected_events == found_events

        # Check the timeline
        if validate_timeline and not wait_for(check_events, async_timeout, async_sleep):
            raise Exception("Timeline issue.")
