import logging

from api.config import async_sleep, async_timeout, validate_tasks
from api.timers import wait_for

from .tasks import AbstractUserTask

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
        filtered_steps = list(filter(lambda step: step is not None, steps))

        user_task_log = []
        for step in filtered_steps:
            # Give Spiff some time to do async processing.
            # Keep retrying untill we have a timeout
            if hasattr(step, "is_ready") and not wait_for(
                lambda: step.is_ready(self.client, self), async_timeout, async_sleep
            ):
                raise Exception(f"Step ({step}) is not ready for case {self}.")

            result = step.run(self.client, self)
            if isinstance(step, AbstractUserTask):
                user_task_log.append(result)

            # Append a timeline event for the step if expected
            if hasattr(step, "event") and step.event:
                self.timeline.append(step.event)

        # Check due_dates
        # logger.info(f"user_task_log = {user_task_log}")
        # for user_task in user_task_log:
        #     task = get_task_by_name(user_task["task_name"])
        #     today = (
        #         datetime.now()
        #         .astimezone()
        #         .replace(hour=0, minute=0, second=0, microsecond=0)
        #     )
        #     expected = (today + task.due_date).timestamp()
        #     due_date = parser.parse(user_task["due_date"]).timestamp()

        #     logger.info(
        #         f"Compare user_task's due_date '{due_date}' with expected '{expected}' (based on {task.due_date})"
        #     )
        #     if not expected == due_date:
        #         raise Exception("Due date issue.")

        def check_tasks():
            """
            Check if the event is added to the timeline and if due-date is accurate.
            """
            events = self.client.get_case_events(self.data["id"])
            expected_events = (
                list(map(lambda event: event.type, self.timeline)) + extra_events
            )
            found_events = list(map(lambda event: event["type"], events))

            logger.info(f"Finding events for case id {self.data['id']} ...")
            logger.info(f"Expected events:\n{expected_events}\nFound:\n{found_events}")

            return expected_events == found_events

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
