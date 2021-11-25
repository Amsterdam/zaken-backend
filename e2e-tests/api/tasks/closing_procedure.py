import logging

from api.config import ReopenRequest, ReviewReopenRequest, SummonTypes
from api.tasks import GenericUserTask
from api.tasks.summon import test_verwerk_aanschrijving
from api.timers import WaitForTimer
from api.user_tasks import (
    task_beoordelen_heropeningsverzoek,
    task_contacteren_eigenaar_1,
    task_contacteren_eigenaar_2,
    task_monitoren_heropeningsverzoek,
    task_monitoren_nieuw_heropeningsverzoek,
    task_opslaan_brandweeradvies,
    task_opslaan_heropeningsverzoek,
    task_opslaan_sleutelteruggave_formulier,
)

logger = logging.getLogger(__name__)


class test_opslaan_brandweeradvies(GenericUserTask, task_opslaan_brandweeradvies):
    @staticmethod
    def get_steps():
        return [
            *test_verwerk_aanschrijving.get_steps(
                type=SummonTypes.HolidayRental.CLOSURE
            ),
            __class__(),
        ]


class test_monitoren_heropeningsverzoek(
    GenericUserTask, task_monitoren_heropeningsverzoek
):
    def __init__(self, reopen_request_received=ReopenRequest.ACCEPTED):
        data = {"heropeningsverzoek_binnengekomen": {"value": reopen_request_received}}
        super(test_monitoren_heropeningsverzoek, self).__init__(**data)

    @staticmethod
    def get_steps():
        return [
            *test_opslaan_brandweeradvies.get_steps(),
            __class__(reopen_request_received=ReopenRequest.ACCEPTED),
        ]


class test_contacteren_eigenaar_1(GenericUserTask, task_contacteren_eigenaar_1):
    @staticmethod
    def get_steps():
        return [*test_monitoren_heropeningsverzoek.get_steps(), __class__()]


class test_beoordelen_heropeningsverzoek(
    GenericUserTask, task_beoordelen_heropeningsverzoek
):
    def __init__(self, review_request=ReviewReopenRequest.ACCEPTED):
        data = {"beoordeling_verzoek": {"value": review_request}}
        super(test_beoordelen_heropeningsverzoek, self).__init__(**data)

    @staticmethod
    def get_steps(review_request=ReviewReopenRequest.ACCEPTED):
        return [
            *test_monitoren_heropeningsverzoek.get_steps(),
            __class__(review_request=review_request),
        ]


class test_monitoren_nieuw_heropeningsverzoek(
    GenericUserTask, task_monitoren_nieuw_heropeningsverzoek
):
    def __init__(self, review_request=ReopenRequest.ACCEPTED):
        data = {"nieuw_heropenings_verzoek": {"value": review_request}}

        super(test_monitoren_nieuw_heropeningsverzoek, self).__init__(**data)

    @staticmethod
    def get_steps():
        return [
            *test_beoordelen_heropeningsverzoek.get_steps(
                review_request=ReviewReopenRequest.DECLINED
            ),
            __class__(nieuw_heropenings_verzoek=ReopenRequest.ACCEPTED),
        ]


class test_contacteren_eigenaar_2(GenericUserTask, task_contacteren_eigenaar_2):
    @staticmethod
    def get_steps():
        return [
            *test_monitoren_nieuw_heropeningsverzoek.get_steps(),
            WaitForTimer(),
            __class__(),
        ]


class test_opslaan_heropeningsverzoek(GenericUserTask, task_opslaan_heropeningsverzoek):
    @staticmethod
    def get_steps():
        return [*test_beoordelen_heropeningsverzoek.get_steps(), __class__()]


class test_opslaan_sleutelteruggave_formulier(
    GenericUserTask, task_opslaan_sleutelteruggave_formulier
):
    @staticmethod
    def get_steps():
        return [*test_beoordelen_heropeningsverzoek.get_steps(), __class__()]
