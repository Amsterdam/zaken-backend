import datetime
import logging

from api import events
from api.config import Action, DaySegment, Priority, Situations, Violation, WeekSegment
from api.tasks import AbstractUserTask, GenericUserTask
from api.user_tasks import (
    task_aanvragen_machtiging,
    task_doorgeven_status_top,
    task_inplannen_status,
    task_monitoren_binnenkomen_machtiging,
)

logger = logging.getLogger(__name__)


class test_aanvragen_machtiging(GenericUserTask, task_aanvragen_machtiging):
    @staticmethod
    def get_steps():
        from api.tasks.debrief import test_verwerken_debrief

        return [
            *test_verwerken_debrief.get_steps(
                violation=Violation.ADDITIONAL_VISIT_WITH_AUTHORIZATION
            ),
            __class__(),
        ]


class test_monitoren_binnenkomen_machtiging(
    GenericUserTask, task_monitoren_binnenkomen_machtiging
):
    @staticmethod
    def get_steps():
        return [*test_aanvragen_machtiging.get_steps(), __class__()]


class test_inplannen_status(AbstractUserTask, task_inplannen_status):
    event = events.ScheduleEvent
    endpoint = "schedules"

    def __init__(
        self,
        action=Action.HOUSE_VISIT,
        week_segment=WeekSegment.WEEKDAY,
        day_segment=DaySegment.DAYTIME,
        priority=Priority.HIGH,
    ):
        super(test_inplannen_status, self).__init__(
            action=action,
            week_segment=week_segment,
            day_segment=day_segment,
            priority=priority,
        )

    @staticmethod
    def get_steps():
        # No preceiding step, case was just created
        return [__class__()]

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "case_user_task_id": task["case_user_task_id"],
        }


class test_doorgeven_status_top(AbstractUserTask, task_doorgeven_status_top):
    endpoint = "visits"
    event = events.VisitEvent

    def __init__(
        self,
        authors=[],
        start_time=None,
        situation=Situations.ACCESS_GRANTED,
        can_next_visit_go_ahead=False,
    ):
        super(test_doorgeven_status_top, self).__init__(
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
            *test_inplannen_status.get_steps(),
            __class__(
                situation=situation, can_next_visit_go_ahead=can_next_visit_go_ahead
            ),
        ]

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "task": task["case_user_task_id"],
        }
