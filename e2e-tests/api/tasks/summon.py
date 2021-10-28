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
from api.tasks.debrief import CheckNotices
from api.timers import WaitForTimer


class ProcessNotice(AbstractUserTask):
    asynchronous = True
    event = events.SummonEvent
    endpoint = "summons"
    task_name = "task_create_summon"
    description = "Verwerk aanschrijving"

    def __init__(
        self,
        type=SummonTypes.HolidayRental.LEGALIZATION_LETTER,
        persons=None,
    ):
        super(ProcessNotice, self).__init__(
            type=type,
            persons=persons if persons else [get_person()],
        )

    @staticmethod
    def get_steps(type=SummonTypes.HolidayRental.LEGALIZATION_LETTER):
        return [
            *CheckNotices.get_steps(),
            __class__(type=type),
        ]

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "case_user_task_id": task["case_user_task_id"],
        }


class MonitorIncomingView(GenericUserTask):
    task_name = "task_monitor_incoming_point_of_view"
    description = "Monitoren binnenkomen zienswijze"

    def __init__(self, civilian_objection_received=True):
        data = {
            "is_civilian_objection_received": {"value": civilian_objection_received}
        }

        super(MonitorIncomingView, self).__init__(**data)

    @staticmethod
    def get_steps(civilian_objection_received=True):
        return [
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.INTENTION_TO_FINE),
            __class__(civilian_objection_received=civilian_objection_received),
        ]


class CheckIncomingView(GenericUserTask):
    task_name = "task_check_incoming_point_of_view"
    description = "Controleren binnenkomst zienswijze"

    def __init__(self, objection=ObjectionReceived.NO):
        data = {"is_civilian_objection_received": {"value": objection}}

        super(CheckIncomingView, self).__init__(**data)

    @staticmethod
    def get_steps(objection=ObjectionReceived.NO):
        return [
            *MonitorIncomingView.get_steps(
                civilian_objection_received=False
            ),  # TODO: This does not work
            __class__(objection=objection),
        ]


class JudgeView(GenericUserTask):
    task_name = "task_judge_point_of_view"
    description = "Beoordelen zienswijze"

    def __init__(self, objection_valid=ObjectionValid.YES):
        data = {"is_citizen_objection_valid": {"value": objection_valid}}
        super(JudgeView, self).__init__(**data)

    @staticmethod
    def get_steps(objection_valid=ObjectionValid.YES):
        return [
            *MonitorIncomingView.get_steps(),
            __class__(objection_valid=objection_valid),
        ]


class MonitorIncomingPermitRequest(GenericUserTask):
    task_name = "task_monitor_incoming_permit_application"
    description = "Monitoren binnenkomen vergunningaanvraag"

    @staticmethod
    def get_steps(permit_requested=True):
        return [
            *ProcessNotice.get_steps(
                type=SummonTypes.HolidayRental.LEGALIZATION_LETTER
            ),
            __class__() if permit_requested else WaitForTimer(),
        ]


class CheckIncomingPermitRequest(GenericUserTask):
    task_name = "task_check_incoming_permit_application"
    description = "Controleren binnenkomst vergunningaanvraag"

    def __init__(self, permit_requested=PermitRequested.NO):
        data = {"action_civilian_permit_requested": {"value": permit_requested}}
        super(CheckIncomingPermitRequest, self).__init__(**data)

    @staticmethod
    def get_steps(permit_requested=PermitRequested.NO):
        return [
            *MonitorIncomingPermitRequest.get_steps(),
            __class__(permit_requested=permit_requested),
        ]


class NoPermit(GenericUserTask):
    task_name = "task_no_permit"
    description = "Geen vergunning"

    @staticmethod
    def get_steps():
        return [
            *CheckIncomingPermitRequest.get_steps(permit_requested=PermitRequested.NO),
            __class__(),
        ]


class MonitorPermitProcedure(GenericUserTask):
    task_name = "task_monitor_permit_request_procedure"
    description = "Monitoren vergunningsprocedure"

    def __init__(self):
        data = {"civilian_has_gotten_permit": {"value": True}}
        super(MonitorPermitProcedure, self).__init__(**data)

    @staticmethod
    def get_steps(has_permit=True):
        return [
            *MonitorIncomingPermitRequest.get_steps(),
            __class__() if has_permit else WaitForTimer(),
        ]


class CheckPermitProcedure(GenericUserTask):
    task_name = "task_check_incoming_permit_application"
    description = "Controleren vergunningsprocedure"

    def __init__(self, permit_requested=PermitRequested.YES):
        data = {"action_civilian_permit_requested": {"value": permit_requested}}
        super(CheckPermitProcedure, self).__init__(**data)

    @staticmethod
    def get_steps(permit_requested=PermitRequested.YES):
        return [
            *MonitorPermitProcedure.get_steps(has_permit=False),
            WaitForTimer(),
            __class__(permit_requested=permit_requested),
        ]


class FinishPermitCheck(GenericUserTask):
    task_name = "task_afronden_vergunningscheck"
    description = "Afronden vergunningscheck"

    @staticmethod
    def get_steps():
        return [
            *CheckPermitProcedure.get_steps(),
            __class__(),
        ]
