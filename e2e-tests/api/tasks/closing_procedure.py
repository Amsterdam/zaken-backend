import logging

from api.config import ReviewRequest, SummonTypes
from api.tasks import GenericUserTask
from api.tasks.summon import ProcessNotice
from api.timers import WaitForTimer

logger = logging.getLogger("api")


class SaveFireBrigadeAdvice(GenericUserTask):
    # task_name = "task_save_fireman_advice"
    asynchronous = True
    task_name = "Activity_19r9rzm"  # BUG in Spiff, should be renamed
    description = "Opslaan brandweeradvies"

    @staticmethod
    def get_steps():
        return [
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.CLOSURE),
            __class__(),
        ]


class MonitorReopeningRequest(GenericUserTask):
    # task_name = "task_monitor_reopening_request"
    task_name = "Activity_0wienly"  # BUG in Spiff, should be renamed
    description = "Monitoren heropeningsverzoek"

    @staticmethod
    def get_steps():
        return [
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.CLOSURE),
            __class__(),
        ]


class ContactOwner(GenericUserTask):
    # task_name = "task_contact_owner"
    task_name = "Activity_0gjczg7"  # BUG in Spiff, should be renamed
    description = "Contacteren eigenaar"

    @staticmethod
    def get_steps():
        return [*MonitorReopeningRequest.get_steps(), WaitForTimer(), __class__()]


class JudgeReopeningRequest(GenericUserTask):
    # task_name = "task_judge_reopening_request"
    task_name = "Activity_0fp5tdz"  # BUG in Spiff, should be renamed
    description = "Beoordelen heropeningsverzoek"

    def __init__(self, review_request=ReviewRequest.ACCEPTED):
        data = {"beoordeling_verzoek": {"value": review_request}}

        super(JudgeReopeningRequest, self).__init__(**data)

    @staticmethod
    def get_steps(review_request=ReviewRequest.ACCEPTED):
        return [
            *SaveFireBrigadeAdvice.get_steps(),
            __class__(review_request=review_request),
        ]


class MonitorReopeningRequestToBeDelivered(GenericUserTask):
    # task_name = "task_monitor_new_reopening_request"
    task_name = "Activity_0zh0d0s"  # BUG in Spiff, should be renamed
    description = "Monitoren nieuw aan te leveren heropeningsverzoek"

    @staticmethod
    def get_steps():
        return [
            *JudgeReopeningRequest.get_steps(review_request=ReviewRequest.DECLINED),
            __class__(),
        ]


class Reopen(GenericUserTask):
    # task_name = "task_reopening"
    task_name = "Activity_1fovs3d"  # BUG in Spiff, should be renamed
    description = "Heropenen"

    @staticmethod
    def get_steps():
        return [*JudgeReopeningRequest.get_steps(), __class__()]


class ScheduleRecheck(GenericUserTask):
    # task_name = "task_schedule_recheck"
    task_name = "Activity_1tmqvpn"  # BUG in Spiff, should be renamed
    description = "Uitzetten hercontrole"

    @staticmethod
    def get_steps():
        return [*Reopen.get_steps(), __class__()]
