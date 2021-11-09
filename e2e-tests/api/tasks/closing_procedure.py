import logging

from api.config import ReopenRequest, ReviewReopenRequest, SummonTypes
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

    def __init__(self, reopen_request_received=ReopenRequest.ACCEPTED):
        data = {"heropeningsverzoek_binnengekomen": {"value": reopen_request_received}}

        super(MonitorReopeningRequest, self).__init__(**data)

    @staticmethod
    def get_steps():
        return [
            *SaveFireBrigadeAdvice.get_steps(),
            __class__(reopen_request_received=ReopenRequest.ACCEPTED),
        ]


class ContactOwnerFirst(GenericUserTask):
    task_name = "task_contacteren_eigenaar_1"
    description = "Contacteren eigenaar"

    @staticmethod
    def get_steps():
        return [*MonitorReopeningRequest.get_steps(), __class__()]


class JudgeReopeningRequest(GenericUserTask):
    task_name = "task_beoordelen_heropeningsverzoek"
    description = "Beoordelen heropeningsverzoek"

    def __init__(self, review_request=ReviewReopenRequest.ACCEPTED):
        data = {"beoordeling_verzoek": {"value": review_request}}

        super(JudgeReopeningRequest, self).__init__(**data)

    @staticmethod
    def get_steps(review_request=ReviewReopenRequest.ACCEPTED):
        return [
            *MonitorReopeningRequest.get_steps(),
            __class__(review_request=review_request),
        ]


class MonitorReopeningRequestToBeDelivered(GenericUserTask):
    task_name = "task_monitoren_nieuw_heropeningsverzoek"
    description = "Monitoren nieuw aan te leveren heropeningsverzoek"

    def __init__(self, review_request=ReopenRequest.ACCEPTED):
        data = {"nieuw_heropenings_verzoek": {"value": review_request}}

        super(MonitorReopeningRequestToBeDelivered, self).__init__(**data)

    @staticmethod
    def get_steps():
        return [
            *JudgeReopeningRequest.get_steps(
                review_request=ReviewReopenRequest.DECLINED
            ),
            __class__(nieuw_heropenings_verzoek=ReopenRequest.ACCEPTED),
        ]


class ContactOwnerSecond(GenericUserTask):
    task_name = "task_contacteren_eigenaar_2"
    description = "Contacteren eigenaar"

    @staticmethod
    def get_steps():
        return [
            *MonitorReopeningRequestToBeDelivered.get_steps(),
            WaitForTimer(),
            __class__(),
        ]


class SaveReopenRequest(GenericUserTask):
    task_name = "task_opslaan_heropeningsverzoek"
    description = "Opslaan heropeningsverzoek"

    @staticmethod
    def get_steps():
        return [*JudgeReopeningRequest.get_steps(), __class__()]


class ReturnKey(GenericUserTask):
    task_name = "task_opslaan_sleutelteruggave_formulier"
    description = "Opslaan sleutelteruggave formulier"

    @staticmethod
    def get_steps():
        return [*JudgeReopeningRequest.get_steps(), __class__()]
