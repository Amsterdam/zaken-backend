from apps.cases.models import Case
from apps.debriefings.models import Debriefing
from django.contrib.auth import get_user_model


class DebriefingTestMixin:
    def create_case(self):
        case = Case.objects.create()
        return case

    def create_user(self):
        USER_EMAIL = "foo@foo.com"
        user_model = get_user_model()
        user = user_model.objects.create(email=USER_EMAIL)
        return user

    def create_debriefing(self):
        case = self.create_case()
        author = self.create_user()
        violation = Debriefing.VIOLATION_YES
        feedback = "Feedback text lorem ipsum"

        debriefing = Debriefing.objects.create(
            case=case, author=author, violation=violation, feedback=feedback
        )

        return debriefing
