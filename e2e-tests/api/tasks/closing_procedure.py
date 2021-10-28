import logging

from api.config import ReviewRequest, SummonTypes
from api.tasks import GenericUserTask
from api.tasks.summon import ProcessNotice
from api.timers import WaitForTimer

logger = logging.getLogger("api")


class SaveFireBrigadeAdvice(GenericUserTask):
    asynchronous = True
    task_name = "task_opslaan_brandweeradvies"
    description = "Opslaan brandweeradvies"

    @staticmethod
    def get_steps():
        return [
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.CLOSURE),
            __class__(),
        ]


class MonitorReopeningRequest(GenericUserTask):
    task_name = "task_monitoren_heropeningsverzoek"
    description = "Monitoren heropeningsverzoek"

    @staticmethod
    def get_steps():
        return [
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.CLOSURE),
            __class__(),
        ]


class ContactOwner(GenericUserTask):
    task_name = "task_contacteren_eigeneer"
    description = "Contacteren eigenaar"

    @staticmethod
    def get_steps():
        return [*MonitorReopeningRequest.get_steps(), WaitForTimer(), __class__()]


class JudgeReopeningRequest(GenericUserTask):
    task_name = "task_beoordelen_heropeningsverzoek"
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
    task_name = "task_monitoren_nieuw_heropeningsverzoek"
    description = "Monitoren nieuw aan te leveren heropeningsverzoek"

    @staticmethod
    def get_steps():
        return [
            *JudgeReopeningRequest.get_steps(review_request=ReviewRequest.DECLINED),
            __class__(),
        ]


class Reopen(GenericUserTask):
    task_name = "task_heropenen"
    description = "Heropenen"

    @staticmethod
    def get_steps():
        return [*JudgeReopeningRequest.get_steps(), __class__()]
