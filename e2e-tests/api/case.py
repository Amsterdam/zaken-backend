import logging
from datetime import datetime

from api.config import async_sleep, async_timeout, validate_tasks
from api.timers import wait_for

logger = logging.getLogger(__name__)


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

    def run_steps(self, *steps, extra_events=[]):
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

        def check_tasks():
            """
            Check if the event is added to the timeline and if due-date is accurate.
            """
            events = self.client.get_case_events(self.data["id"])
            expected_events = (
                list(map(lambda event: event.type, self.timeline)) + extra_events
            )
            found_events = list(map(lambda event: event["type"], events))

            logging.info(f"Finding events for case id {self.data['id']} ...")
            logging.info(f"Expected events:\n{expected_events}\nFound:\n{found_events}")

            due_dates_accurate = True
            user_tasks = self.client.get_case_tasks(self.data["id"])
            logging.info("Check due_dates on all tasks")
            for i, step in enumerate(steps):
                expected = str(datetime.now() + step.due_date)
                logging.info(f"- expected = {expected}")
                if not expected == user_tasks[i]["due_date"]:
                    logging.info(f"-- failure! it's {user_tasks[i]['due_date']}")
                    due_dates_accurate = False
                    break

            return expected_events == found_events and due_dates_accurate

        # Check the timeline
        if validate_tasks and not wait_for(check_tasks, async_timeout, async_sleep):
            raise Exception("Timeline issue.")

    def add_process(self, process):
        return self.client.call(
            "post",
            f"/cases/{self.data['id']}/processes/start/",
            {"workflow_option_id": process},
            task_name="create_case",
        )
