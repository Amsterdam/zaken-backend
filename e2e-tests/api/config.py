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
timer_duration = 20 + 2 + 5  # timer itself + heartbeat + buffer
async_sleep = 0.5  # in seconds
async_timeout = 5  # in seconds


class Themes:
    HOLIDAY_RENTAL = 2


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
    NOTIFICATION = 4


class Violation:
    NO = "NO"
    YES = "YES"
    SEND_TO_OTHER_THEME = "SEND_TO_OTHER_THEME"
    ADDITIONAL_RESEARCH_REQUIRED = "ADDITIONAL_RESEARCH_REQUIRED"
    ADDITIONAL_VISIT_REQUIRED = "ADDITIONAL_VISIT_REQUIRED"
    ADDITIONAL_VISIT_WITH_AUTHORIZATION = "ADDITIONAL_VISIT_WITH_AUTHORIZATION"


class NextStep:
    RECHECK = "hercontrole"
    CLOSE = "sluiten"
    # RENOUNCE = "renounce"  # TODO where did this came from? It's no longer supported?


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


class SummonTypes:
    class HolidayRental:
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


class DecisionType:
    class HolidayRental:
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
    class HolidayRental:
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
