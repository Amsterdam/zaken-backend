import logging
import sys
from datetime import datetime, timedelta, timezone

from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

DEFAULT_USER_TASK_DUE_DATE = relativedelta(weeks=1)


class BpmnField:
    def __init__(self, _user_task, **kwargs):
        args = ["label", "name", "options", "type", "required", "tooltip"]
        if not isinstance(_user_task, user_task) and not kwargs.keys() in args:
            raise Exception
        self.label = kwargs.get("label")
        self.options = kwargs.get("options")
        self.name = kwargs.get("name")
        self.type = kwargs.get("type")
        self.required = kwargs.get("required")
        self.tooltip = kwargs.get("tooltip")
        self.user_task = _user_task

    def get_value(self, k):
        return (
            getattr(self.user_task, f"field__{self.name}__{k}")
            if hasattr(self.user_task, f"field__{self.name}__{k}")
            else getattr(self, k)
        )

    @property
    def asdict(self):
        d = dict(
            (k, self.get_value(k))
            for k in ["label", "options", "type", "required", "tooltip"]
        )
        d.update({"name": self.name})
        return d


class BpmnForm:
    user_task = None

    def __init__(self, user_task_instance):
        if not isinstance(user_task_instance, user_task):
            raise Exception
        self.user_task = user_task_instance

    @property
    def form(self):
        form = self.user_task.case_user_task.form
        if hasattr(self.user_task, "form"):
            form = self.user_task.form
        elif form and isinstance(form, list):
            form = [
                BpmnField(_user_task=self.user_task, **field).asdict for field in form
            ]
        return form


def get_task_by_name(task_name):
    current_module = sys.modules[__name__]
    user_tasks = list(
        filter(lambda class_name: class_name[:5] == "task_", dir(current_module))
    )

    for ut in user_tasks:
        cls = getattr(current_module, ut)
        if cls.get_task_name() == task_name:
            return cls
    return user_task


class user_task:

    # It would be nice if all tasks implement their own due_date, but for
    # now we'll set a default as well.
    due_date = DEFAULT_USER_TASK_DUE_DATE
    case_user_task = None

    def __init__(self, case_user_task_instance):
        from .models import CaseUserTask

        if not isinstance(case_user_task_instance, CaseUserTask):
            raise Exception
        self.case_user_task = case_user_task_instance

    @classmethod
    def get_due_date(cls, case):
        return getattr(cls, "due_date")

    @classmethod
    def get_task_name(cls):
        return getattr(cls, "_task_name", cls.__name__)

    def get_form(self):
        return BpmnForm(self)

    def get_data(self):
        return {}

    def mapped_form_data(self, data):
        return {}

    def instance_created(self):
        return


class task_inplannen_status(user_task):
    """
    Inplannen ${status_name}

    'Inplannen hercontrole' is not different from 'Inplannen huisbezoek' atm
    """

    _task_name = "task_create_schedule"
    due_date = relativedelta(weeks=1)


class task_bepalen_processtap(user_task):
    """Bepalen processtap"""

    due_date = relativedelta(days=2)


class task_bepalen_processtap_standaard(user_task):
    """Bepalen processtap"""

    due_date = relativedelta(days=2)


class task_aanvragen_machtiging(user_task):
    """Aanvragen machtiging"""

    _task_name = "task_request_authorization"
    due_date = relativedelta(days=2)


class task_terugkoppelen_melder(user_task):
    """Terugkoppelen melder"""

    due_date = relativedelta(days=2)


class task_terugkoppelen_melder_1(user_task):
    """
    Terugkoppelen melder

    Er zijn totaal 3 terugkoppelingen mogelijk:
    - eerste
    - tweede
    - eind
    """

    due_date = relativedelta(days=2)


class task_terugkoppelen_melder_2(user_task):
    """Terugkoppelen melder"""

    due_date = relativedelta(days=2)


class task_sia_terugkoppeling_melders_legacy(user_task):
    """SIA terugkoppeling melder(s)"""

    _task_name = "Activity_19a40xb"
    due_date = relativedelta(days=2)


class task_doorgeven_status_top(user_task):
    """Doorgeven ${status_name} TOP"""

    _task_name = "task_create_visit"

    due_date = relativedelta(months=2)

    @classmethod
    def get_due_date(cls, case_user_task):
        due_date = super().get_due_date(case_user_task)
        latest_schedule = case_user_task.case.schedules.order_by("date_modified").last()
        if latest_schedule and latest_schedule.visit_from_datetime:
            extra_days = timedelta(
                days=(
                    latest_schedule.visit_from_datetime
                    - datetime.now(timezone(timedelta(hours=0)))
                ).days
                + 1
            )
            return due_date + extra_days
        return due_date


class task_create_debrief(user_task):
    """Verwerken debrief"""

    due_date = relativedelta(days=1)


class task_create_debrief_leegstand(user_task):
    """Verwerken debrief"""

    due_date = relativedelta(days=1)


class task_afwachten_intern_onderzoek(user_task):
    """Afwachten intern onderzoek"""

    _task_name = "task_wait_internal_reasearch"
    due_date = relativedelta(weeks=2)


class task_narekenen_service_kosten(user_task):
    """Narekenen onredelijke servicekosten"""

    _task_name = "task_recalulate_service_costs"
    due_date = relativedelta(weeks=2)


class task_verstuur_uitnodiging_gesprek(user_task):
    """Versturen uitnodiging gesprek"""

    _task_name = "task_send_conversation_invitation"
    due_date = relativedelta(weeks=2)


class task_uitvoeren_gesprek_verhuurder(user_task):
    """Uitvoeren gesprek verhuurder"""

    _task_name = "task_conduct_conversation_landlord"
    due_date = relativedelta(weeks=2)


class task_wait_for_advise_other_discipline(user_task):
    pass


class task_rappelleren_advies_andere_discipline(user_task):
    """Rappelleren advies andere discipline"""

    _task_name = "task_reminder_advise_other_discipline"
    due_date = relativedelta(days=7)


class task_opvragen_stukken(user_task):
    """Opvragen stukken"""

    _task_name = "task_request_documents"
    due_date = relativedelta(weeks=2)


class task_wait_for_documents(user_task):
    pass


class task_rappelleren_opgevraagde_stukken(user_task):
    """Rappelleren opgevraagde stukken"""

    _task_name = "task_reminder_documents"
    due_date = relativedelta(days=7)


class task_opstellen_verkorte_rapportage_huisbezoek(user_task):
    """Opstellen verkorte rapportage huisbezoek"""

    _task_name = "task_prepare_abbreviated_visit_rapport"
    due_date = relativedelta(days=3)


class task_opstellen_beeldverslag(user_task):
    """Opstellen beeldverslag"""

    _task_name = "task_create_picture_rapport"
    due_date = relativedelta(days=3)


class task_opstellen_rapport_van_bevindingen(user_task):
    """Opstellen rapport van bevindingen"""

    _task_name = "task_create_report_of_findings"
    due_date = relativedelta(days=3)


class task_opstellen_concept_aanschrijving(user_task):
    """Opstellen concept aanschrijving"""

    _task_name = "task_create_concept_summons"
    due_date = relativedelta(weeks=2)

    def instance_created(self):
        from apps.cases.models import CaseState

        CaseState.objects.get_or_create(
            case=self.case_user_task.case,
            status=CaseState.CaseStateChoice.HANDHAVING,
        )
        return


class task_nakijken_aanschrijving(user_task):
    """Nakijken aanschrijving"""

    _task_name = "task_check_summons"
    due_date = relativedelta(weeks=1)


class task_afzien_concept_aanschrijving(user_task):
    """Afzien concept aanschrijving"""

    due_date = relativedelta(weeks=1)


class task_verwerk_aanschrijving(user_task):
    """Verwerk aanschrijving"""

    _task_name = "task_create_summon"
    due_date = relativedelta(days=2)


class task_monitoren_binnenkomen_machtiging(user_task):
    """Monitoren binnenkomen machtiging"""

    _task_name = "task_monitor_incoming_authorization"


class task_monitoren_binnenkomen_vergunningaanvraag(user_task):
    """Monitoren binnenkomen vergunningaanvraag"""

    _task_name = "task_monitor_incoming_permit_application"
    due_date = relativedelta(weeks=0)


class task_controleren_binnenkomst_vergunningaanvraag(user_task):
    """Controleren binnenkomst vergunningaanvraag"""

    _task_name = "task_check_incoming_permit_application"
    due_date = relativedelta(weeks=2)


class task_monitoren_vergunningsprocedure(user_task):
    """Monitoren vergunningsprocedure"""

    _task_name = "task_monitor_permit_request_procedure"
    due_date = relativedelta(weeks=0)


class task_controleren_vergunningsprocedure(user_task):
    """Controleren vergunningsprocedure"""

    _task_name = "Activity_1gaa36w"
    due_date = relativedelta(weeks=2)


class task_afronden_vergunningscheck(user_task):
    """Afronden vergunningscheck"""

    due_date = relativedelta(days=1)


class task_monitoren_binnenkomen_zienswijze(user_task):
    """Monitoren binnenkomen zienswijze"""

    _task_name = "task_monitor_incoming_point_of_view"
    due_date = relativedelta(days=0)


class task_controleren_binnenkomst_zienswijze(user_task):
    """Controleren binnenkomst zienswijze"""

    _task_name = "task_check_incoming_point_of_view"
    due_date = relativedelta(weeks=1)


class task_beoordelen_zienswijze(user_task):
    """Beoordelen zienswijze"""

    _task_name = "task_judge_point_of_view"
    due_date = relativedelta(weeks=2)


class task_opstellen_concept_voornemen_afzien(user_task):
    """Opstellen concept voornemen afzien"""

    due_date = relativedelta(weeks=2)
    _task_name = "task_create_concept_renounce"


class task_nakijken_afzien_voornemen(user_task):
    """Nakijken afzien voornemen"""

    _task_name = "task_check_renounce_letter"
    due_date = relativedelta(weeks=1)


class task_verwerken_definitieve_voornemen_afzien(user_task):
    """Verwerken definitieve voornemen afzien"""

    _task_name = "task_create_definitive_renounce"
    due_date = relativedelta(days=2)


class task_opstellen_concept_besluit(user_task):
    """Opstellen concept besluit"""

    _task_name = "task_make_concept_decision"
    due_date = relativedelta(weeks=2)


class task_nakijken_besluit(user_task):
    """Nakijken besluit"""

    _task_name = "task_check_concept_decision"
    due_date = relativedelta(weeks=1)


class task_verwerken_definitieve_besluit(user_task):
    """Verwerken definitieve besluit"""

    _task_name = "task_create_decision"
    due_date = relativedelta(days=2)


class task_versturen_invordering_belastingen_goed_verhuurderschap(user_task):
    """Versturen invordering belastingen"""

    _task_name = "task_send_tax_collection_theme_goed_verhuurderschap"
    due_date = relativedelta(weeks=2)


class task_besluit_openbaarmaking_namen(user_task):
    """Besluit openbaarmaking namen"""

    _task_name = "task_take_decision_publicate_names"
    due_date = relativedelta(weeks=2)


class task_opstellen_besluit_openbaarmaking_namen(user_task):
    """Opstellen besluit openbaarmaking namen"""

    _task_name = "task_create_decision_publicate_names"
    due_date = relativedelta(weeks=2)


class task_nakijken_besluit_openbaarmaking_namen(user_task):
    """Nakijken besluit openbaarmaking namen"""

    _task_name = "task_check_decision_publicate_names"
    due_date = relativedelta(weeks=2)


class task_verwerken_besluit_openbaarmaking_namen(user_task):
    """Verwerken besluit openbaar-making namen"""

    _task_name = "task_process_decision_publicate_names"
    due_date = relativedelta(weeks=2)


class task_monitoren_voorlopige_voorziening(user_task):
    """Monitoren voorlopige voorziening"""

    _task_name = "task_wait_response_publicate_names"
    due_date = relativedelta(weeks=2)


class task_publiceren_namen(user_task):
    """Publiceren namen"""

    _task_name = "task_publicate_names"
    due_date = relativedelta(weeks=2)


class task_versturen_invordering_belastingen(user_task):
    """Versturen invordering belastingen"""

    _task_name = "task_send_tax_collection"
    due_date = relativedelta(weeks=2)


class task_contacteren_stadsdeel(user_task):
    """Contacteren stadsdeel"""

    _task_name = "task_contact_city_district"
    due_date = relativedelta(weeks=1)


class task_verwerken_snel_besluit(user_task):
    """Verwerken snel besluit"""

    _task_name = "task_create_quick_decision"
    due_date = relativedelta(days=2)


class task_uitzetten_vervolgstap(user_task):
    """Uitzetten vervolgstap"""

    _task_name = "task_set_next_step"
    due_date = relativedelta(weeks=2)


class task_opslaan_brandweeradvies(user_task):
    """Opslaan brandweeradvies"""

    due_date = relativedelta(days=2)


class task_monitoren_heropeningsverzoek(user_task):
    """Monitoren heropeningsverzoek"""

    due_date = relativedelta(weeks=0)


class task_contacteren_eigenaar_1(user_task):
    """Contacteren eigenaar"""

    due_date = relativedelta(weeks=1)


class task_contacteren_eigenaar_2(user_task):
    """Contacteren eigenaar"""

    due_date = relativedelta(weeks=1)


class task_opslaan_heropeningsverzoek(user_task):
    """Opslaan heropeningsverzoek"""

    due_date = relativedelta(weeks=2)


class task_opslaan_sleutelteruggave_formulier(user_task):
    """Opslaan sleutelteruggave formulier"""

    due_date = relativedelta(weeks=2)


class task_beoordelen_heropeningsverzoek(user_task):
    """Beoordelen heropeningsverzoek"""

    due_date = relativedelta(weeks=1)


class task_monitoren_nieuw_heropeningsverzoek(user_task):
    """Monitoren nieuw aan te leveren heropeningsverzoek"""

    due_date = relativedelta(weeks=0)


class task_nieuwe_melding_verwerken(user_task):
    """Nieuwe melding verwerken"""

    _task_name = "task_create_signal"
    due_date = relativedelta(weeks=1)


class task_oppakken_correspondentie(user_task):
    """Oppakken correspondentie"""

    _task_name = "task_correspondence"
    due_date = relativedelta(weeks=2)


class task_oppakken_opheffen_openbaarmaking_namen(user_task):
    """Opheffen openbaarmaking namen"""

    _task_name = "task_opheffen_openbaarmaking_namen"
    due_date = relativedelta(weeks=2)


class task_oppakken_terugbelverzoek(user_task):
    """Oppakken terugbelverzoek"""

    _task_name = "task_callback_request"
    due_date = relativedelta(days=1)


class task_aanleveren_bezwaardossier(user_task):
    """Aanleveren bezwaardossier"""

    _task_name = "task_submit_objectionfile"
    due_date = relativedelta(weeks=1)


class task_add_extra_information(user_task):
    """Verwerken extra informatie"""


class task_close_case(user_task):
    """Afsluiten zaak"""

    due_date = relativedelta(weeks=1)


class task_afwachten_casus_overleg(user_task):
    """Afwachten casus overleg"""

    _task_name = "task_afwachten_casus_overleg"
    due_date = relativedelta(weeks=1)


class task_sub_workflow_opstellen_digitale_analyse(user_task):
    due_date = relativedelta(days=3)


class task_opstelllen_rapport_van_bevindingen_1(user_task):
    due_date = relativedelta(days=3)


class task_create_picture_rapport_1(user_task):
    due_date = relativedelta(days=3)


class task_opstellen_digitale_analyse(user_task):
    due_date = relativedelta(days=3)


class task_create_picture_rapport_2(user_task):
    due_date = relativedelta(days=3)


class task_opstelllen_rapport_van_bevindingen_2(user_task):
    due_date = relativedelta(days=3)


# leegstand tasks
class task_opstellen_verzoek_tot_inlichtingen(user_task):
    due_date = relativedelta(days=3)


class task_opstellen_aanschrijving_eigenaar(user_task):
    due_date = relativedelta(days=7)


class task_controleren_binnenkomen_reactie(user_task):
    due_date = relativedelta(days=7)


class task_inplannen_leegstandsgesprek(user_task):
    due_date = relativedelta(days=7)


class task_controleren_binnenkomen_melding(user_task):
    due_date = relativedelta(days=7)


class task_opstellen_vorderingsbrief(user_task):
    due_date = relativedelta(days=7)


class task_monitoren_binnenkomen_reactie_vordering(user_task):
    due_date = relativedelta(days=18)


class task_versturen_afspraakbrief(user_task):
    due_date = relativedelta(days=3)


class task_leegstand_opstellen_rapport_van_bevindingen(user_task):
    due_date = relativedelta(days=3)


class task_leegstand_opstellen_beeldverslag(user_task):
    due_date = relativedelta(days=3)


class task_opstellen_leegstandsbeschikking(user_task):
    due_date = relativedelta(days=7)

    # It's possible to bypass task_opstellen_concept_aanschrijving for theme Leegstand.
    # Create the CaseState HANDHAVING if it doesn't exist. Otherwise, the status TOEZICHT is retained.
    def instance_created(self):
        from apps.cases.models import CaseState

        CaseState.objects.get_or_create(
            case=self.case_user_task.case,
            status=CaseState.CaseStateChoice.HANDHAVING,
        )
        return


class task_opstellen_constateringsbrief(user_task):
    due_date = relativedelta(days=7)


class task_nakijken_constateringsbrief(user_task):
    due_date = relativedelta(days=7)


class task_verwerken_constateringsbrief(user_task):
    due_date = relativedelta(days=7)


class task_uitvoeren_leegstandsgesprek(user_task):
    due_date = relativedelta(weeks=4)


class task_uitvoeren_administratief_onderzoek(user_task):
    due_date = relativedelta(weeks=2)


class task_sub_workflow_terugkoppelen_bi(user_task):
    due_date = relativedelta(days=1)


class task_aanleveren_wob_dossier(user_task):
    due_date = relativedelta(days=3)


class task_1_sia_terugkoppeling_melders(user_task):
    due_date = relativedelta(days=2)


class task_2_sia_terugkoppeling_melders(user_task):
    due_date = relativedelta(days=2)


class task_sia_terugkoppeling_melders(user_task):
    due_date = relativedelta(days=2)


class task_doorzetten_adres_naar_corporatie(user_task):
    due_date = relativedelta(days=7)


class task_monitoren_reactie_corporatie_voor_huisbezoek(user_task):
    pass


class task_contacteren_corporatie_voor_huisbezoek(user_task):
    due_date = relativedelta(days=2)


class task_afwachten_besluit_corporatie_na_huisbezoek_1(user_task):
    pass


class task_verwerken_constatering_corporatie(user_task):
    due_date = relativedelta(days=7)


class task_verwerken_reactie_corporatie(user_task):
    due_date = relativedelta(days=7)


class task_contacteren_corporatie_na_huisbezoek(user_task):
    due_date = relativedelta(days=2)


class task_afwachten_besluit_corporatie_na_huisbezoek_2(user_task):
    pass


class task_melder_contact_verlenging_termijn(user_task):
    due_date = relativedelta(days=3)


class task_kwaliteitscheck_rapporten(user_task):
    due_date = relativedelta(days=14)


class task_opsturen_rapport_naar_corporatie_overtreding(user_task):
    due_date = relativedelta(days=14)


class task_afwachten_overgaan_tot_handhaven(user_task):
    pass


class task_opsturen_rapport_naar_corporatie(user_task):
    due_date = relativedelta(days=1)


class task_verwerken_resultaat_corporatie(user_task):
    due_date = relativedelta(days=2)


class task_verwerken_uitkomst_corporatie(user_task):
    due_date = relativedelta(days=56)


class task_ontvangen_reactie_corporatie(user_task):
    due_date = relativedelta(months=1)


class task_close_case_concept(user_task):
    @staticmethod
    def get_due_date(case_user_task):
        from apps.decisions.models import Decision

        non_renounced_decisions = Decision.objects.filter(
            case=case_user_task.case
        ).exclude(decision_type__workflow_option="no_decision")

        return (
            relativedelta(months=13)
            if non_renounced_decisions.count()
            else relativedelta(weeks=1)
        )


class task_opstellen_intrekkingen(user_task):
    due_date = relativedelta(days=1)


class task_nakijken_intrekkingen(user_task):
    due_date = relativedelta(days=2)


class task_verwerken_en_opsturen_besluit(user_task):
    due_date = relativedelta(days=1)

    @property
    def form(self):
        decisions = self.case_user_task.case.decisions.exclude(
            decision_type__workflow_option="no_decision"
        ).order_by("date_added")
        if not decisions:
            return [
                {
                    "label": "Er zijn geen besluiten in te trekken.",
                    "name": "geen_besluiten",
                }
            ]
        return [
            {
                "label": "Welk besluit(en) wil je intrekken?",
                "name": "besluiten_intrekken",
                "options": [{"label": t.__str__(), "value": t.id} for t in decisions],
                "type": "multiselect",
            },
            {
                "label": "Toelichting (niet verplicht)",
                "name": "toelichting",
                "options": [],
                "type": "text",
            },
        ]

    def get_data(self):
        decisions = list(
            self.case_user_task.case.decisions.filter(
                sanction_id__isnull=False,
                active=False,
            ).values_list("id", flat=True)
        )
        return {
            "ingetrokken_sancties": decisions,
        }

    def mapped_form_data(self, data):
        from apps.decisions.models import Decision

        decisions = (
            self.case_user_task.case.decisions.all()
            .order_by("date_added")
            .filter(
                id__in=data.get("besluiten_intrekken", {}).get("value", []),
            )
        )
        for d in decisions:
            d.active = False
        Decision.objects.bulk_update(
            decisions,
            [
                "active",
            ],
        )
        return {
            "besluiten_intrekken": {
                "label": "Ingetrokken besluit(en)",
                "value": list(t.__str__() for t in decisions),
            },
            "toelichting": {
                "value": data.get("toelichting", {}).get("value"),
                "label": "Toelichting",
            },
        }


class task_intrekken_vorderingen(user_task):
    due_date = relativedelta(days=1)


class task_rapport_bewoners(user_task):
    due_date = relativedelta(days=2)


class task_lod_opheffen(user_task):
    due_date = relativedelta(days=2)


# handhavingsverzoek
class task_controleren_of_gemeente_in_gebreke_is(user_task):
    due_date = relativedelta(days=2)


class task_opstellen_brief_ongeldige_ingebrekestelling(user_task):
    due_date = relativedelta(days=1)


class task_nakijken_brief_ongeldige_ingebrekestelling(user_task):
    due_date = relativedelta(days=1)


class task_verturen_brief_ongeldige_ingebrekestelling(user_task):
    due_date = relativedelta(days=1)


class task_opsturen_verlenging_beslistermijn(user_task):
    due_date = relativedelta(days=1)


class task_nakijken_verlenging_beslistermijn(user_task):
    due_date = relativedelta(days=1)


class task_verwerken_verlenging_beslistermijn(user_task):
    due_date = relativedelta(days=1)


class task_controleren_juistheid_aanvraag(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_afwijzen(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_juist_nakijken_afwijzing(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_juist_verwerken_afwijzing(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_opstellen_buiten_behandeling_laten(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_nakijken_buiten_behandeling_laten(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_verwerken_buiten_behandeling_laten(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_opstellen_ontvangstbevestiging(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_nakijken_ontvangstbevestiging(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_verwerken_ontvangstbevestiging(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_aangeven_uitkomst_debrief(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_opstellen_afwijzing(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_onjuist_nakijken_afwijzing(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_verwerken_afwijzing(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_aangeven_uitkomst(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_opstellen_besluit_afwijzing(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_nakijken_besluit_afwijzing(user_task):
    due_date = relativedelta(days=1)


class task_handhavingsverzoek_verwerken_besluit_afwijzing(user_task):
    due_date = relativedelta(days=1)


class task_set_next_step_digital_surveillance(user_task):
    due_date = relativedelta(weeks=2)


class task_set_next_step_administratieve_hercontrole(user_task):
    due_date = relativedelta(weeks=2)


class task_uitvoeren_digitale_hercontrole(user_task):
    due_date = relativedelta(weeks=1)


class task_administrative_hercontrole(user_task):
    due_date = relativedelta(weeks=1)


class task_opstellen_verslag_digitale_hercontrole(user_task):
    due_date = relativedelta(days=3)
