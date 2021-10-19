import logging
import os

# Setup logging
loglevel = os.environ.get("LOGLEVEL", "WARNING")
logging.basicConfig(level=loglevel)

api_config = {
    "host": os.environ.get("API_HOST", "http://localhost:8080/api/v1"),
}

validate_timeline = False
timer_duration = 4  # in seconds
async_sleep = 1.5  # in seconds
async_timeout = 10  # in seconds


class Themes:
    HOLIDAY_RENTAL = 1


class DaySegment:
    DAYTIME = 1
    AT_NIGHT = 2


class WeekSegment:
    WEEKDAY = 1
    WEEKEND = 2


class Action:
    HOUSE_VISIT = 1
    RECHECK = 2


class Priority:
    HIGH = 1
    NORMAL = 2


class Reason:
    NOTIFICATION = 1


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
    RENOUNCE = "renounce"


class ReviewRequest:
    DECLINED = "afgekeurd"
    ACCEPTED = "goedgekeurd"


class SummonTypes:
    class HolidayRental:
        LEGALIZATION_LETTER = 14  # Legalisatiebrief
        OBLIGATION_TO_REPORT_INTENTION_TO_FINE = 8  # Meldplicht voornemen boete
        CLOSURE = 13  # Sluiting
        WARNING_LETTER = 15  # Waarschuwingsbrief

        ADVANCE_ANNOUNCEMENT_DURING_SUM = 5  # Vooraankondiging dwangsom
        INTENTION_TO_FINE = 6  # Voornemen boete
        INTENTION_TO_WITHDRAW_BB_LICENCE = 11  # Voornemen intrekking BB-vergunning
        INTENTION_TO_WITHDRAW_SS_LICENCE = 10  # Voornemen intrekking SS-vergunning
        INTENTION_TO_WITHDRAW_VV_LICENCE = 12  # Voornemen intrekking VV-vergunning
        INTENTION_TO_RECOVER_DENSITY = 7  # Voornemen invordering dwangsom
        INTENDED_PREVENTIVE_BURDEN = 9  # Voornemen preventieve last
        WARNING_BB_LICENSE = 3  # Waarschuwing BB-vergunning
        WARNING_SS_LICENCE = 2  # Waarschuwing SS-vergunning
        WARNING_VV_LICENSE = 1  # Waarschuwing VV-vergunning


class DecisionType:
    class HolidayRental:
        FINE = 1  # Boete
        COLLECTION_PENALTY = 2  # Invordering dwangsom
        DECISION_FINE_REPORT_DUTY = 3  # Meldplicht beschikking dwangsom
        PREVENTIVE_BURDEN = 4  # Preventieve last
        BURDEN_UNDER_PENALTY = 5  # Last onder dwangsom
        REVOKE_VV_PERMIT = 6  # Intrekken VV vergunning
        REVOKE_BB_PERMIT = 7  # Intrekken BB vergunning
        REVOKE_SHORTSTAY_PERMIT = 8  # Intrekken Shortstay vergunning
        NO_DECISION = 9  # Afzien voornemen


class CloseReason:
    class HolidayRental:
        DIFFERENT = 14  # Anders, vermeld in toelichting
        FORWARDED_TO_ANOTHER_TEAM = 10  # Doorgezet naar ander team
        NO_REASON_TO_VISIT_AGAIN = 9  # Geen aanleiding adres opnieuw te bezoeken
        NO_FROUD = 11  # Geen woonfraude
        NOT_ENOUGH_PROOF = 12  # Onvoldoende bewijs
        RESULT_AFTER_RECHECK = 13  # Resultaat na hercontrole


class Objection:
    NO = "no_objection_not_received"
    YES = "yes_objection_received"


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
