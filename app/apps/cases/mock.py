import datetime

from apps.addresses.models import Address
from apps.cases.models import Case, CaseReason, CaseState, CaseStateType, CaseTeam
from apps.debriefings.models import Debriefing
from apps.visits.models import Visit
from django.conf import settings
from django.contrib.auth import get_user_model
from model_bakery import baker


def mock_cases():
    start_date_day_before = datetime.datetime.now().replace(
        hour=10, minute=0, second=0, microsecond=0
    ) - datetime.timedelta(days=2)
    start_date_yesterday = datetime.datetime.now().replace(
        hour=10, minute=0, second=0, microsecond=0
    ) - datetime.timedelta(days=1)
    start_date_today = datetime.datetime.now().replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    start_date_today_but_later = datetime.datetime.now().replace(
        hour=17, minute=0, second=0, microsecond=0
    )
    case_state_type_not_walked, _ = CaseStateType.objects.get_or_create(
        name="Nog niet gelopen"
    )
    case_state_type_no_one, _ = CaseStateType.objects.get_or_create(
        name="Niemand aanwezig"
    )
    case_state_type_access_granted, _ = CaseStateType.objects.get_or_create(
        name="Toegang verleend"
    )

    # These should exist due to a data migration
    team = CaseTeam.objects.get(name=settings.DEFAULT_TEAM)
    reason = CaseReason.objects.get(name=settings.DEFAULT_REASON)
    address = Address.get("0363200012145295")

    user_model = get_user_model()
    user_1, _ = user_model.objects.get_or_create(
        email="jake.gyllenhaal@example.com",
        first_name="Jake",
        last_name="Gyllenhaal",
    )
    user_2, _ = user_model.objects.get_or_create(
        email="jessica.chastain@example.com",
        first_name="Jessica",
        last_name="Chastain",
    )

    authors = user_model.objects.filter(id__in=[user_1.id, user_2.id])

    cases = baker.make(
        Case,
        author=user_1,
        reason=reason,
        team=team,
        start_date=datetime.date.today() - datetime.timedelta(days=2),
        address=address,
        description="Melding gedaan door de buren",
        _quantity=7,
    )

    for case in cases:
        baker.make(
            CaseState,
            status=case_state_type_not_walked,
            state_date=start_date_day_before,
            case=case,
        )

    for case in cases[1:]:
        baker.make(
            CaseState,
            status=case_state_type_no_one,
            state_date=start_date_yesterday,
            case=case,
        )
        baker.make(
            Visit,
            case=case,
            start_time=start_date_yesterday,
            situation=Visit.SITUATION_NOBODY_PRESENT,
            suggest_next_visit="Weekend",
            suggest_next_visit_description="Ziet er uit als feesthuis. Grote pakkans in het weekend",
            observations=[
                "malfunctioning_doorbell",
                "vacant",
                "hotel_furnished",
            ],
            notes="Ziet er uit als feesthuis. Grote pakkans in het weekend",
            authors=authors,
        )

    # add today state to all newer result cases
    for case in cases[2:]:
        baker.make(
            CaseState,
            status=case_state_type_access_granted,
            state_date=start_date_today,
            case=case,
        )

    for case in cases[2:5]:
        baker.make(
            Visit,
            case=case,
            start_time=start_date_today,
            situation=Visit.SITUATION_ACCESS_GRANTED,
            authors=authors,
            notes="Hit. Er zaten 8 toeristen in het gebouw.",
            observations=[],
        )

    baker.make(
        Debriefing, author=user_1, case=cases[3], violation=Debriefing.VIOLATION_YES
    )

    baker.make(
        Debriefing,
        author=user_1,
        case=cases[4],
        violation=Debriefing.VIOLATION_ADDITIONAL_RESEARCH_REQUIRED,
    )

    # Nog een huisbezoek vereist
    for case in cases[5:7]:
        baker.make(
            Debriefing,
            author=user_2,
            case=case,
            violation=Debriefing.VIOLATION_ADDITIONAL_VISIT_REQUIRED,
        )

    baker.make(
        Visit,
        case=cases[6],
        start_time=start_date_today_but_later,
        authors=authors,
        situation=Visit.SITUATION_ACCESS_GRANTED,
        notes="Extra bezoek was zeker vruchtbaar. Flyers + printout van de advertentie gevonden. Genoeg bewijs om over te gaan op handhaving",
        observations=[],
    )
