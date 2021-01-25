from apps.cases.models import Case
from apps.debriefings.models import Debriefing
from django.contrib.auth import get_user_model
from model_bakery import baker


class DebriefingTestMixin:
    def create_case(self):
        case = baker.make(Case)
        return case

    def create_user(self):
        USER_EMAIL = "foo@foo.com"
        user_model = get_user_model()
        user = baker.make(user_model, email=USER_EMAIL)
        return user

    def create_debriefing(self):
        case = self.create_case()
        author = self.create_user()
        violation = Debriefing.VIOLATION_YES
        debriefing = baker.make(
            Debriefing, case=case, author=author, violation=violation
        )

        return debriefing
