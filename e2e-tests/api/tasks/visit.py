import datetime
import logging

from api import events
from api.config import Action, DaySegment, Priority, Situations, WeekSegment
from api.tasks import AbstractUserTask, GenericUserTask

logger = logging.getLogger("api")


class RequestAuthorization(GenericUserTask):
    task_name = "task_request_authorization"
    description = "Aanvragen machtiging"
    # asynchronous = True  # TODO should be async right?

    @staticmethod
    def get_steps():
        return [
            # No preceiding step, case was just created
            __class__(),
        ]


class MonitorIncomingAuthorization(GenericUserTask):
    task_name = "task_monitor_incoming_authorization"
    description = "Monitoren binnenkomen machtiging"

    @staticmethod
    def get_steps():
        return [*RequestAuthorization.get_steps(), __class__()]


class ScheduleVisit(AbstractUserTask):
    asynchronous = True
    event = events.ScheduleEvent
    endpoint = "schedules"
    task_name = "task_create_schedule"
    description = "Inplannen $status_name"

    def __init__(
        self,
        action=Action.HOUSE_VISIT,
        week_segment=WeekSegment.WEEKDAY,
        day_segment=DaySegment.DAYTIME,
        priority=Priority.HIGH,
    ):
        super(ScheduleVisit, self).__init__(
            action=action,
            week_segment=week_segment,
            day_segment=day_segment,
            priority=priority,
        )

    @staticmethod
    def get_steps():
        return [
            # No preceiding step, case was just created
            __class__()
        ]

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "case_user_task_id": task["case_user_task_id"],
        }


class Visit(AbstractUserTask):
    event = events.VisitEvent
    endpoint = "visits"
    task_name = "task_create_visit"
    description = "Doorgeven $status_name TOP"

    def __init__(
        self,
        authors=[],
        start_time=None,
        situation=Situations.ACCESS_GRANTED,
        can_next_visit_go_ahead=False,
    ):
        super(Visit, self).__init__(
            authors=authors,
            start_time=start_time if start_time else str(datetime.datetime.now()),
            situation=situation,
            can_next_visit_go_ahead=can_next_visit_go_ahead,
        )

    @staticmethod
    def get_steps(
        situation=Situations.ACCESS_GRANTED,
        can_next_visit_go_ahead=False,
    ):
        return [
            *ScheduleVisit.get_steps(),
            __class__(
                situation=situation, can_next_visit_go_ahead=can_next_visit_go_ahead
            ),
        ]

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "task": task["case_user_task_id"],
        }
