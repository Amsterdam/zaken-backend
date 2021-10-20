from api import events
from api.config import HasPermit, Objection, PermitRequested, SummonTypes
from api.mock import get_person
from api.tasks import AbstractUserTask, GenericUserTask
from api.tasks.debrief import CheckNotices


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
        # data = {"is_civilian_objection_received": {"value": objection}}

        super(MonitorIncomingView, self).__init__()

    @staticmethod
    def get_steps():
        return [
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.INTENTION_TO_FINE),
            __class__(),
        ]


class CheckIncomingView(GenericUserTask):
    task_name = "task_check_incoming_point_of_view"
    description = "Controleren binnenkomst zienswijze"

    def __init__(self, objection=Objection.NO):
        data = {"is_civilian_objection_received": {"value": objection}}

        super(CheckIncomingView, self).__init__(**data)

    @staticmethod
    def get_steps(objection=Objection.NO):
        return [
            *MonitorIncomingView.get_steps(),
            __class__(objection=objection),
        ]


class JudgeView(GenericUserTask):
    task_name = "task_judge_point_of_view"
    description = "Beoordelen zienswijze"

    def __init__(self, objection_valid=True):
        data = {"is_citizen_objection_valid": {"value": objection_valid}}

        super(JudgeView, self).__init__(**data)

    @staticmethod
    def get_steps(objection_valid=True):
        return [
            *MonitorIncomingView.get_steps(),
            __class__(objection_valid=objection_valid),
        ]


class MonitorIncomingPermitRequest(GenericUserTask):
    task_name = "task_monitor_incoming_permit_application"
    description = "Monitoren binnenkomen vergunningaanvraag"

    @staticmethod
    def get_steps(objection_valid=True):
        return [
            *CheckIncomingView.get_steps(),
            __class__(),
        ]


class CheckIncomingPermitRequest(GenericUserTask):
    task_name = "Activity_1t8h57c"  # BUG in Spiff, should be renamed
    description = "Controleren binnenkomst vergunningaanvraag"

    def __init__(self, permit_requested=PermitRequested.NO):
        data = {"action_civilian_permit_requested": {"value": permit_requested}}
        super(CheckIncomingView, self).__init__(**data)

    @staticmethod
    def get_steps(permit_requested=PermitRequested.NO):
        return [
            *MonitorIncomingPermitRequest.get_steps(),
            __class__(permit_requested=permit_requested),
        ]


class NoPermitRequested(GenericUserTask):
    task_name = "Activity_0c3s2q7"  # BUG in Spiff, should be renamed
    description = "Geen vergunning"

    @staticmethod
    def get_steps():
        return [
            *CheckIncomingPermitRequest.get_steps(permit_requested=PermitRequested.NO),
            __class__(),
        ]


class MonitorPermitProcedure(GenericUserTask):
    task_name = "Activity_1k03k9a"  # BUG in Spiff, should be renamed
    description = "Monitoren vergunningsprocedure"

    @staticmethod
    def get_steps(has_permit=True):
        return [
            *MonitorIncomingPermitRequest.get_steps(),
            __class__(has_permit=has_permit),
        ]


class CheckPermitProcedure(GenericUserTask):
    task_name = "Activity_1gaa36w"  # BUG in Spiff, should be renamed
    description = "Controleren vergunningsprocedure"

    def __init__(self, has_permit=HasPermit.YES):
        data = {"civilian_has_gotten_permit": {"value": has_permit}}
        super(CheckIncomingView, self).__init__(**data)

    @staticmethod
    def get_steps(has_permit=HasPermit.YES):
        return [
            *MonitorPermitProcedure.get_steps(),
            __class__(has_permit=has_permit),
        ]


class FinishPermitCheck(GenericUserTask):
    task_name = "Activity_18x19gf"  # BUG in Spiff, should be renamed
    description = "Afronden vergunningscheck"

    @staticmethod
    def get_steps():
        return [
            *CheckPermitProcedure.get_steps(),
            __class__(),
        ]
