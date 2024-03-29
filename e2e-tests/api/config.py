import logging
import os

# By default skipTest are skipped, you can override this behavior with NO_SKIP=1
skip_tests = not os.getenv("NO_SKIP", "False").lower() in ("true", "1", "t")

# If you don't want to validate if the timeline is correct you can skip checks. Will be a bit faster
validate_tasks = not os.getenv("NO_VALIDATE", "False").lower() in ("true", "1", "t")

# Setup logging
loglevel = os.environ.get("LOGLEVEL", "WARNING")
logging.basicConfig(level=loglevel)

# API configuration
api_config = {
    "host": os.environ.get("API_HOST", "http://localhost:8080/api/v1"),
}

# Timers and async waits
timer_duration = 20 + 2 + 13  # timer itself + heartbeat + buffer
async_sleep = 1  # in seconds
async_timeout = 40  # in seconds


class Theme:
    VAKANTIEVERHUUR = 2
    KAMERVERHUUR = 3
    ONDERMIJNING = 4


class DaySegment:
    DAYTIME = 4
    AT_NIGHT = 3


class WeekSegment:
    WEEKDAY = 3
    WEEKEND = 4


class Action:
    HOUSE_VISIT = 2
    RECHECK = 3


class Priority:
    HIGH = 4
    NORMAL = 5


class Reason:
    class Vakantieverhuur:
        NOTIFICATION = 4

    class Ondermijning:
        SIA_MELDING = 7
        EIGEN_ONDERZOEK = 8
        MMA = 9
        POLITIE = 10
        ANDER_TEAM = 11

    class HolidayRental:
        PROJECT = 2
        NOTIFICATION = 4


class Violation:
    NO = "NO"
    YES = "YES"
    SEND_TO_OTHER_THEME = "SEND_TO_OTHER_THEME"
    ADDITIONAL_RESEARCH_REQUIRED = "ADDITIONAL_RESEARCH_REQUIRED"
    ADDITIONAL_VISIT_REQUIRED = "ADDITIONAL_VISIT_REQUIRED"
    ADDITIONAL_VISIT_WITH_AUTHORIZATION = "ADDITIONAL_VISIT_WITH_AUTHORIZATION"
    LIKELY_INHABITED = "LIKELY_INHABITED"


class TypeConceptSummon:
    OTHER_SUMMON = "aanschrijvingen"
    RENOUNCE_SUMMON = "afzien_aanschrijving"


class Subject:
    class Ondermijning:
        CRIMINEEL_GEBRUIK = 1
        HENNEP = 2
        OVERIGE_WOONFRAUDE = 3

    class HolidayRental:
        GEEN_NACHTVERBLIJF = 4
        NIET_MELDEN = 5
        ONTBREKEN_INSCHRIJVING_BRP = 6
        ONTBREKEN_REGISTRATIENUMMER = 7
        ONTBREKEN_VV_VERGUNNING = 8
        OVERSCHRIJDING_NACHTEN = 9
        OVERSCHRIJDING_PERSONEN = 10
        SCHENDING_OPPERVLAKTE_EISEN = 11
        VV_IN_SOCIALE_HUURWONING = 12
        VV_ZONDER_FEITELIJKE_BEWONING = 13

    class Kamerverhuur:
        MEER_DAN_HET_TOEGESTANE_AANTAL_HUISHOUDENS = 14
        KORTDUREND_VERBLIJF = 15
        CRIMINEEL_GEBRUIK = 16
        HENNEP = 17
        OVERIGE_WOONFRAUDE = 18
        VERBOUWD_NAAR_TWEE_OF_MEER_ZELFSTANDIGE_WONINGEN = 19
        SAMENVOEGING_VAN_WONINGEN = 20


class SummonValidity:
    YES = "ja"
    NO = "nee"


class RenounceConceptSummon:
    NEW_CONCEPT_SUMMON = "concept_aanschrijving"
    NO_VIOLATION = "geen_overtreding"
    NEW_VISIT_REQUIRED = "nieuw_huisbezoek"


class NextStep:
    RECHECK = "hercontrole"
    CLOSE = "sluiten"
    # RENOUNCE = "renounce"  # TODO where did this came from? It's no longer supported?


class VisitNextStep:
    VISIT_WITH_AUTHORIZATION = "visit_with_authorization"
    VISIT_WITHOUT_AUTHORIZATION = "visit_without_authorization"
    NO_VISIT = "no_visit"


class ReopenRequest:
    ACCEPTED = "Yes"
    DECLINED = "No"


class ReviewReopenRequest:
    ACCEPTED = "goedgekeurd"
    DECLINED = "afgekeurd"


class Process:
    class HolidayRental:
        ADD_SUMMON = 8  # aanschrijving_toevoegen
        # START_OBJECTION_FILE_PROCESS = ?  # start_objectionfile_process
        # ALL_APPLICATIONS_AND_DECISIONS_COMPLETED = ?  # alle_aanschrijvingen_en_beslissingen_afgerond
        # START_CORRESPONDENCE_PROCESS = ?  # start_correspondence_process
        # START_EXTRA_INFORMATION = ?  # start_extra_information
        # START_NUISANCE_PROCESS = ?  # start_nuisance_process
        # START_SIGNAL_PROCESS = ?  # start_signal_process
        # START_CALLBACK_REQUEST_PROCESS = ?  # start_callbackrequest_process


class SummonType:
    class Vakantieverhuur:
        LEGALIZATION_LETTER = 14  # Legalisatiebrief
        OBLIGATION_TO_REPORT_INTENTION_TO_FINE = 15  # Meldplicht voornemen boete
        CLOSURE = 16  # Sluiting
        ADVANCE_ANNOUNCEMENT_DURING_SUM = 18  # Vooraankondiging dwangsom
        INTENTION_TO_FINE = 18  # Voornemen boete
        INTENTION_TO_WITHDRAW_BB_LICENCE = 19  # Voornemen intrekking BB-vergunning
        INTENTION_TO_WITHDRAW_SS_LICENCE = (
            20  # Voornemen intrekking SS-vergunning. X: Why is it called this...
        )
        INTENTION_TO_WITHDRAW_VV_LICENCE = 21  # Voornemen intrekking VV-vergunning
        INTENTION_TO_RECOVER_DENSITY = 22  # Voornemen invordering dwangsom
        INTENDED_PREVENTIVE_BURDEN = 23  # Voornemen preventieve last
        WARNING_BB_LICENSE = 24  # Waarschuwing BB-vergunning
        WARNING_SS_LICENCE = 25  # Waarschuwing SS-vergunning
        WARNING_VV_LICENSE = 26  # Waarschuwing VV-vergunning

    class Leegstand:
        LEGALIZATION_LETTER = 36  # Legalisatiebrief
        INTENTION_TO_FINE = 37  # Voornemen boete
        ADVANCE_ANNOUNCEMENT_DURING_SUM = 38  # Vooraankondiging dwangsom
        LEEGSTAND_BESCHIKKING = 39  # Vooraankondiging dwangsom
        LEEGSTANDSBRIEF = 40  # Leegstandsbrief


class DecisionType:
    class Vakantieverhuur:
        FINE = 9  # Boete
        COLLECTION_PENALTY = 13  # Invordering dwangsom
        DECISION_FINE_REPORT_DUTY = 15  # Meldplicht beschikking dwangsom
        PREVENTIVE_BURDEN = 16  # Preventieve last
        BURDEN_UNDER_PENALTY = 14  # Last onder dwangsom
        REVOKE_VV_PERMIT = 12  # Intrekken VV vergunning
        REVOKE_BB_PERMIT = 10  # Intrekken BB vergunning
        REVOKE_SHORTSTAY_PERMIT = 11  # Intrekken Shortstay vergunning
        NO_DECISION = 21  # Afzien voornemen


class CloseReason:
    class Vakantieverhuur:
        DIFFERENT = 15  # Anders, vermeld in toelichting
        FORWARDED_TO_ANOTHER_TEAM = 16  # Doorgezet naar ander team
        NO_REASON_TO_VISIT_AGAIN = 17  # Geen aanleiding adres opnieuw te bezoeken
        NO_FROUD = 18  # Geen woonfraude
        NOT_ENOUGH_PROOF = 19  # Onvoldoende bewijs
        RESULT_AFTER_RECHECK = 20  # Resultaat na hercontrole


class ObjectionReceived:
    NO = "no_objection_not_received"
    YES = "yes_objection_received"


class ObjectionValid:
    NO = "no_citizen_objection_not_valid"
    YES = "yes_citizen_objection_valid"


class Situations:
    NOBODY_PRESENT = "nobody_present"
    NO_COOPERATION = "no_cooperation"
    ACCESS_GRANTED = "access_granted"


class PermitRequested:
    NO = "no_action"
    YES = "yes_permit_requested"


class HasPermit:
    NO = "no_permit"
    YES = "yes_permit"
