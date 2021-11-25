from api import events
from api.config import (
    HasPermit,
    ObjectionReceived,
    ObjectionValid,
    PermitRequested,
    SummonTypes,
)
from api.mock import get_person
from api.tasks import AbstractUserTask, GenericUserTask
from api.tasks.debrief import test_nakijken_aanschrijvingen
from api.timers import WaitForTimer
from api.user_tasks import (
    task_afronden_vergunningscheck,
    task_beoordelen_zienswijze,
    task_controleren_binnenkomst_vergunningaanvraag,
    task_controleren_binnenkomst_zienswijze,
    task_controleren_vergunningsprocedure,
    task_monitoren_binnenkomen_vergunningaanvraag,
    task_monitoren_binnenkomen_zienswijze,
    task_monitoren_vergunningsprocedure,
    task_verwerk_aanschrijving,
)


class test_verwerk_aanschrijving(AbstractUserTask, task_verwerk_aanschrijving):
    event = events.SummonEvent
    endpoint = "summons"

    def __init__(
        self,
        type=SummonTypes.HolidayRental.LEGALIZATION_LETTER,
        persons=None,
    ):
        super(test_verwerk_aanschrijving, self).__init__(
            type=type,
            persons=persons if persons else [get_person()],
        )

    @staticmethod
    def get_steps(type=SummonTypes.HolidayRental.LEGALIZATION_LETTER):
        return [
            *test_nakijken_aanschrijvingen.get_steps(),
            __class__(type=type),
        ]

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "case_user_task_id": task["case_user_task_id"],
        }


class test_monitoren_binnenkomen_zienswijze(
    GenericUserTask, task_monitoren_binnenkomen_zienswijze
):
    def __init__(self, civilian_objection_received=True):
        data = {
            "is_civilian_objection_received": {"value": civilian_objection_received}
        }

        super(test_monitoren_binnenkomen_zienswijze, self).__init__(**data)

    @staticmethod
    def get_steps(civilian_objection_received=True):
        return [
            *test_verwerk_aanschrijving.get_steps(
                type=SummonTypes.HolidayRental.INTENTION_TO_FINE
            ),
            __class__(civilian_objection_received=civilian_objection_received),
        ]


class test_controleren_binnenkomst_zienswijze(
    GenericUserTask, task_controleren_binnenkomst_zienswijze
):
    def __init__(self, objection=ObjectionReceived.NO):
        data = {"is_civilian_objection_received": {"value": objection}}

        super(test_controleren_binnenkomst_zienswijze, self).__init__(**data)

    @staticmethod
    def get_steps(objection=ObjectionReceived.NO):
        return [
            *test_monitoren_binnenkomen_zienswijze.get_steps(
                civilian_objection_received=False
            ),  # TODO: This does not work
            __class__(objection=objection),
        ]


class test_beoordelen_zienswijze(GenericUserTask, task_beoordelen_zienswijze):
    def __init__(self, objection_valid=ObjectionValid.YES):
        data = {"is_citizen_objection_valid": {"value": objection_valid}}
        super(test_beoordelen_zienswijze, self).__init__(**data)

    @staticmethod
    def get_steps(objection_valid=ObjectionValid.YES):
        return [
            *test_monitoren_binnenkomen_zienswijze.get_steps(),
            __class__(objection_valid=objection_valid),
        ]


class test_monitoren_binnenkomen_vergunningaanvraag(
    GenericUserTask, task_monitoren_binnenkomen_vergunningaanvraag
):
    @staticmethod
    def get_steps(permit_requested=True):
        return [
            *test_verwerk_aanschrijving.get_steps(
                type=SummonTypes.HolidayRental.LEGALIZATION_LETTER
            ),
            __class__() if permit_requested else WaitForTimer(),
        ]


class test_controleren_binnenkomst_vergunningaanvraag(
    GenericUserTask, task_controleren_binnenkomst_vergunningaanvraag
):
    def __init__(self, permit_requested=PermitRequested.NO):
        data = {"action_civilian_permit_requested": {"value": permit_requested}}
        super(test_controleren_binnenkomst_vergunningaanvraag, self).__init__(**data)

    @staticmethod
    def get_steps(permit_requested=PermitRequested.NO):
        return [
            *test_monitoren_binnenkomen_vergunningaanvraag.get_steps(),
            __class__(permit_requested=permit_requested),
        ]


class test_monitoren_vergunningsprocedure(
    GenericUserTask, task_monitoren_vergunningsprocedure
):
    def __init__(self):
        data = {"civilian_has_gotten_permit": {"value": True}}
        super(test_monitoren_vergunningsprocedure, self).__init__(**data)

    @staticmethod
    def get_steps(has_permit=True):
        return [
            *test_monitoren_binnenkomen_vergunningaanvraag.get_steps(),
            __class__() if has_permit else WaitForTimer(),
        ]


class test_controleren_vergunningsprocedure(
    GenericUserTask, task_controleren_vergunningsprocedure
):
    def __init__(self, has_permit=HasPermit.YES):
        data = {"civilian_has_gotten_permit": {"value": has_permit}}
        super(test_controleren_vergunningsprocedure, self).__init__(**data)

    @staticmethod
    def get_steps(has_permit=PermitRequested.YES):
        return [
            *test_monitoren_vergunningsprocedure.get_steps(has_permit=False),
            WaitForTimer(),
            __class__(has_permit=has_permit),
        ]


class test_afronden_vergunningscheck(GenericUserTask, task_afronden_vergunningscheck):
    @staticmethod
    def get_steps():
        return [
            *test_controleren_vergunningsprocedure.get_steps(),
            __class__(),
        ]
