from apps.cases.models import Case
from apps.debriefings.models import Debriefing
from apps.users.models import User


class DebriefingTestMixin:
    def create_case(self):
        case = Case.objects.create()
        return case

    def create_user(self):
        USER_EMAIL = "foo@foo.com"
        user = User.objects.create(email=USER_EMAIL)
        return user

    def create_debriefing(self):
        case = self.create_case()
        author = self.create_user()
        violation = True
        feedback = "Feedback text lorem ipsum"

        debriefing = Debriefing.objects.create(
            case=case, author=author, violation=violation, feedback=feedback
        )

        return debriefing
