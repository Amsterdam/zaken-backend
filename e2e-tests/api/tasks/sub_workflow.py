from api.tasks import GenericUserTask
from api.user_tasks import (
    task_aanleveren_bezwaardossier,
    task_add_extra_information,
    task_afwachten_casus_overleg,
    task_nieuwe_melding_verwerken,
    task_oppakken_correspondentie,
    task_oppakken_terugbelverzoek,
    task_sia_terugkoppeling_melders_legacy,
)


class test_nieuwe_melding_verwerken(GenericUserTask, task_nieuwe_melding_verwerken):
    @staticmethod
    def get_steps():
        return [
            # *X.get_steps(),  # TODO what is the preceiding step?
            __class__(),
        ]


class test_sia_terugkoppeling_melders(
    GenericUserTask, task_sia_terugkoppeling_melders_legacy
):
    @staticmethod
    def get_steps():
        return [
            *test_nieuwe_melding_verwerken.get_steps(),
            __class__(),
        ]


class test_oppakken_correspondentie(GenericUserTask, task_oppakken_correspondentie):
    @staticmethod
    def get_steps():
        return [
            # *X.get_steps(),  # TODO what is the preceiding step?
            __class__(),
        ]


class test_oppakken_terugbelverzoek(GenericUserTask, task_oppakken_terugbelverzoek):
    @staticmethod
    def get_steps():
        return [
            # *X.get_steps(),  # TODO what is the preceiding step?
            __class__(),
        ]


class test_aanleveren_bezwaardossier(GenericUserTask, task_aanleveren_bezwaardossier):
    @staticmethod
    def get_steps():
        return [
            # *X.get_steps(),  # TODO what is the preceiding step?
            __class__(),
        ]


class test_add_extra_information(GenericUserTask, task_add_extra_information):
    @staticmethod
    def get_steps():
        return [
            # *X.get_steps(),  # TODO what is the preceiding step?
            __class__(),
        ]


class test_casus_overleg(GenericUserTask, task_afwachten_casus_overleg):
    @staticmethod
    def get_steps():
        return [
            # *X.get_steps(),  # TODO what is the preceiding step?
            __class__(),
        ]
