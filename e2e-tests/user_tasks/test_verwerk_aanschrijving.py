from api.config import SummonType
from api.tasks.close_case import test_uitzetten_vervolgstap
from api.tasks.closing_procedure import test_opslaan_brandweeradvies
from api.tasks.summon import (
    test_monitoren_binnenkomen_vergunningaanvraag,
    test_monitoren_binnenkomen_zienswijze,
    test_nakijken_aanschrijving,
    test_verwerk_aanschrijving,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_verwerk_aanschrijving_test(DefaultAPITest):
    def test_legalization_letter(self):
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.LEGALIZATION_LETTER
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_vergunningaanvraag),
        )

    def test_closing_procedure(self):
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(type=SummonType.Vakantieverhuur.CLOSURE),
            ValidateOpenTasks(test_opslaan_brandweeradvies),
        )

    def test_obligation_to_report_intention_to_fine(self):
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.OBLIGATION_TO_REPORT_INTENTION_TO_FINE
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_zienswijze),
        )

    def test_advance_announcement_during_sum(self):
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.ADVANCE_ANNOUNCEMENT_DURING_SUM
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_zienswijze),
        )

    def test_intention_to_fine(self):
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.INTENTION_TO_FINE
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_zienswijze),
        )

    def test_intention_to_withdraw_bb_licence(self):
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.INTENTION_TO_WITHDRAW_BB_LICENCE
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_zienswijze),
        )

    def test_intention_to_withdraw_ss_licence(self):
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.INTENTION_TO_WITHDRAW_SS_LICENCE
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_zienswijze),
        )

    def test_intention_to_withdraw_vv_licence(self):
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.INTENTION_TO_WITHDRAW_VV_LICENCE
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_zienswijze),
        )

    def test_intention_to_recover_density(self):
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.INTENTION_TO_RECOVER_DENSITY
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_zienswijze),
        )

    def test_intended_preventive_burden(self):
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.INTENDED_PREVENTIVE_BURDEN
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_zienswijze),
        )

    def test_warning_bb_license(self):
        """
        type of 'warning-letter'
        """
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.WARNING_BB_LICENSE
            ),
            ValidateOpenTasks(
                test_uitzetten_vervolgstap
            ),  # TODO should be ScheduleVisit
        )

    def test_warning_ss_licence(self):
        """
        type of 'warning-letter'
        """
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.WARNING_SS_LICENCE
            ),
            ValidateOpenTasks(
                test_uitzetten_vervolgstap
            ),  # TODO should be ScheduleVisit
        )

    def test_warning_vv_license(self):
        """
        type of 'warning-letter'
        """
        self.get_case().run_steps(
            *test_nakijken_aanschrijving.get_steps(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.WARNING_VV_LICENSE
            ),
            ValidateOpenTasks(
                test_uitzetten_vervolgstap
            ),  # TODO should be ScheduleVisit
        )
