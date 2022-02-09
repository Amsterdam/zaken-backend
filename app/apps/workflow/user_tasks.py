import logging
import sys

from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

DEFAULT_USER_TASK_DUE_DATE = relativedelta(weeks=1)


def get_task_by_name(task_name):
    current_module = sys.modules[__name__]
    user_tasks = list(
        filter(lambda class_name: class_name[:5] == "task_", dir(current_module))
    )

    for user_task in user_tasks:
        cls = getattr(current_module, user_task)
        if cls.get_task_name() == task_name:
            return cls


class user_task:

    # It would be nice if all tasks implement their own due_date, but for
    # now we'll set a default as well.
    due_date = DEFAULT_USER_TASK_DUE_DATE

    @classmethod
    def get_due_date(cls, case):
        return getattr(cls, "due_date")

    @classmethod
    def get_task_name(cls):
        return getattr(cls, "_task_name", cls.__name__)


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


class task_sia_terugkoppeling_melders(user_task):
    """SIA terugkoppeling melder(s)"""

    _task_name = "Activity_19a40xb"
    due_date = relativedelta(days=2)


class task_doorgeven_status_top(user_task):
    """Doorgeven ${status_name} TOP"""

    _task_name = "task_create_visit"
    due_date = relativedelta(months=+2)


class task_verwerken_debrief(user_task):
    """Verwerken debrief"""

    _task_name = "task_create_debrief"
    due_date = relativedelta(days=1)


class task_afwachten_intern_onderzoek(user_task):
    """Afwachten intern onderzoek"""

    _task_name = "task_wait_internal_reasearch"
    due_date = relativedelta(weeks=2)


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


class task_versturen_invordering_belastingen(user_task):
    """Versturen invordering belastingen"""

    _task_name = "task_send_tax_collection"
    due_date = relativedelta(weeks=2)


class task_contacteren_stadsdeel(user_task):
    """Contacteren stadsdeel"""

    _task_name = "task_contact_city_district"
    due_date = relativedelta(weeks=1)


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


class task_oppakken_terugbelverzoek(user_task):
    """Oppakken terugbelverzoek"""

    _task_name = "task_callback_request"
    due_date = relativedelta(days=1)


class task_aanleveren_bezwaardossier(user_task):
    """Aanleveren bezwaardossier"""

    _task_name = "task_submit_objectionfile"
    due_date = relativedelta(weeks=1)


class task_verwerken_extra_informatie(user_task):
    """Verwerken extra informatie"""

    _task_name = "task_add_extra_information"


class task_afsluiten_zaak(user_task):
    """Afsluiten zaak"""

    _task_name = "task_close_case"

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


class task_afwachten_casus_overleg(user_task):
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
