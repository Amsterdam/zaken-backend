from api.config import SummonTypes
from api.tasks.close_case import PlanNextStep
from api.tasks.closing_procedure import MonitorReopeningRequest, SaveFireBrigadeAdvice
from api.tasks.debrief import CheckNotices
from api.tasks.summon import (
    MonitorIncomingPermitRequest,
    MonitorIncomingView,
    ProcessNotice,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestSummon(DefaultAPITest):
    def test_legalization_letter(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(type=SummonTypes.HolidayRental.LEGALIZATION_LETTER),
            ValidateOpenTasks(MonitorIncomingPermitRequest),
        )

    def test_closing_procedure(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(type=SummonTypes.HolidayRental.CLOSURE),
            ValidateOpenTasks(SaveFireBrigadeAdvice, MonitorReopeningRequest),
        )

    def test_obligation_to_report_intention_to_fine(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(
                type=SummonTypes.HolidayRental.OBLIGATION_TO_REPORT_INTENTION_TO_FINE
            ),
            ValidateOpenTasks(MonitorIncomingView),
        )

    def test_advance_announcement_during_sum(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(
                type=SummonTypes.HolidayRental.ADVANCE_ANNOUNCEMENT_DURING_SUM
            ),
            ValidateOpenTasks(MonitorIncomingView),
        )

    def test_intention_to_fine(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(type=SummonTypes.HolidayRental.INTENTION_TO_FINE),
            ValidateOpenTasks(MonitorIncomingView),
        )

    def test_intention_to_withdraw_bb_licence(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(
                type=SummonTypes.HolidayRental.INTENTION_TO_WITHDRAW_BB_LICENCE
            ),
            ValidateOpenTasks(MonitorIncomingView),
        )

    def test_intention_to_withdraw_ss_licence(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(
                type=SummonTypes.HolidayRental.INTENTION_TO_WITHDRAW_SS_LICENCE
            ),
            ValidateOpenTasks(MonitorIncomingView),
        )

    def test_intention_to_withdraw_vv_licence(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(
                type=SummonTypes.HolidayRental.INTENTION_TO_WITHDRAW_VV_LICENCE
            ),
            ValidateOpenTasks(MonitorIncomingView),
        )

    def test_intention_to_recover_density(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(type=SummonTypes.HolidayRental.INTENTION_TO_RECOVER_DENSITY),
            ValidateOpenTasks(MonitorIncomingView),
        )

    def test_intended_preventive_burden(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(type=SummonTypes.HolidayRental.INTENDED_PREVENTIVE_BURDEN),
            ValidateOpenTasks(MonitorIncomingView),
        )

    def test_warning_bb_license(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(type=SummonTypes.HolidayRental.WARNING_BB_LICENSE),
            ValidateOpenTasks(PlanNextStep),  # TODO should be ScheduleVisit
        )

    def test_warning_ss_licence(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(type=SummonTypes.HolidayRental.WARNING_SS_LICENCE),
            ValidateOpenTasks(PlanNextStep),  # TODO should be ScheduleVisit
        )

    def test_warning_vv_license(self):
        self.get_case().run_steps(
            *CheckNotices.get_steps(),
            ProcessNotice(type=SummonTypes.HolidayRental.WARNING_VV_LICENSE),
            ValidateOpenTasks(PlanNextStep),  # TODO should be ScheduleVisit
        )
