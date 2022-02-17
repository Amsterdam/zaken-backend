from api import events
from api.config import (
    HasPermit,
    ObjectionReceived,
    ObjectionValid,
    PermitRequested,
    RenounceConceptSummon,
    SummonType,
    SummonValidity,
    TypeConceptSummon,
)
from api.mock import get_person
from api.tasks import AbstractUserTask, GenericUserTask
from api.tasks.debrief import (
    test_opstellen_beeldverslag,
    test_opstellen_rapport_van_bevindingen,
    test_terugkoppelen_melder_2,
)
from api.timers import WaitForTimer
from api.user_tasks import (
    task_afronden_vergunningscheck,
    task_afwachten_intern_onderzoek,
    task_afzien_concept_aanschrijving,
    task_beoordelen_zienswijze,
    task_controleren_binnenkomst_vergunningaanvraag,
    task_controleren_binnenkomst_zienswijze,
    task_controleren_vergunningsprocedure,
    task_monitoren_binnenkomen_vergunningaanvraag,
    task_monitoren_binnenkomen_zienswijze,
    task_monitoren_vergunningsprocedure,
    task_nakijken_aanschrijving,
    task_opstellen_concept_aanschrijving,
    task_verwerk_aanschrijving,
)


class test_opstellen_concept_aanschrijving(
    GenericUserTask, task_opstellen_concept_aanschrijving
):
    def __init__(
        self,
        type_concept_summon=TypeConceptSummon.OTHER_SUMMON,
        description="Concept aanschrijving toelichting",
    ):
        super().__init__(
            type_concept_aanschrijving={"value": type_concept_summon},
            concept_aanschrijving_toelichting={"value": description},
        )

    @staticmethod
    def get_steps(
        type_concept_summon=TypeConceptSummon.OTHER_SUMMON,
        description="Concept aanschrijving toelichting",
    ):
        return [
            *test_opstellen_beeldverslag.get_steps(),
            test_opstellen_rapport_van_bevindingen(),
            __class__(
                type_concept_summon=type_concept_summon,
                description=description,
            ),
        ]


class test_nakijken_aanschrijving(GenericUserTask, task_nakijken_aanschrijving):
    def __init__(self, summon_validity=SummonValidity.YES):
        super().__init__(aanschrijving_valide={"value": summon_validity})

    @staticmethod
    def get_steps(summon_validity=SummonValidity.YES):
        return [
            *test_opstellen_concept_aanschrijving.get_steps(),
            __class__(summon_validity=summon_validity),
        ]


class test_afzien_concept_aanschrijving(
    GenericUserTask, task_afzien_concept_aanschrijving
):
    def __init__(self, renounce_concept_summon=RenounceConceptSummon.NO_VIOLATION):
        super().__init__(
            afzien_concept_aanschrijving={"value": renounce_concept_summon}
        )

    @staticmethod
    def get_steps(renounce_concept_summon=RenounceConceptSummon.NO_VIOLATION):
        return [
            *test_nakijken_aanschrijving.get_steps(summon_validity=SummonValidity.NO),
            __class__(renounce_concept_summon=renounce_concept_summon),
        ]


class test_verwerk_aanschrijving(AbstractUserTask, task_verwerk_aanschrijving):
    event = events.SummonEvent
    endpoint = "summons"

    def __init__(
        self,
        type=SummonType.Vakantieverhuur.LEGALIZATION_LETTER,
        persons=None,
    ):
        super().__init__(
            type=type,
            persons=persons if persons else [get_person()],
        )

    @staticmethod
    def get_steps(type=SummonType.Vakantieverhuur.LEGALIZATION_LETTER):
        return [
            *test_nakijken_aanschrijving.get_steps(),
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
        super().__init__(
            is_civilian_objection_received={"value": civilian_objection_received}
        )

    @staticmethod
    def get_steps(civilian_objection_received=True):
        return [
            *test_verwerk_aanschrijving.get_steps(
                type=SummonType.Vakantieverhuur.INTENTION_TO_FINE
            ),
            __class__(civilian_objection_received=civilian_objection_received),
        ]


class test_controleren_binnenkomst_zienswijze(
    GenericUserTask, task_controleren_binnenkomst_zienswijze
):
    def __init__(self, objection=ObjectionReceived.NO):
        super().__init__(is_civilian_objection_received={"value": objection})

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
        super().__init__(is_citizen_objection_valid={"value": objection_valid})

    @staticmethod
    def get_steps(objection_valid=ObjectionValid.YES):
        return [
            *test_monitoren_binnenkomen_zienswijze.get_steps(),
            __class__(objection_valid=objection_valid),
        ]


class test_monitoren_binnenkomen_vergunningaanvraag(
    GenericUserTask, task_monitoren_binnenkomen_vergunningaanvraag
):
    def __init__(self):

        super().__init__(action_civilian_permit_requested={"value": True})

    @staticmethod
    def get_steps(permit_requested=True):
        return [
            *test_verwerk_aanschrijving.get_steps(
                type=SummonType.Vakantieverhuur.LEGALIZATION_LETTER
            ),
            __class__() if permit_requested else WaitForTimer(),
        ]


class test_controleren_binnenkomst_vergunningaanvraag(
    GenericUserTask, task_controleren_binnenkomst_vergunningaanvraag
):
    def __init__(self, permit_requested=PermitRequested.NO):
        super().__init__(action_civilian_permit_requested={"value": permit_requested})

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
        super().__init__(civilian_has_gotten_permit={"value": True})

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
        super().__init__(civilian_has_gotten_permit={"value": has_permit})

    @staticmethod
    def get_steps(has_permit=PermitRequested.YES):
        return [
            *test_monitoren_vergunningsprocedure.get_steps(has_permit=False),
            WaitForTimer(),
            __class__(has_permit=has_permit),
        ]
