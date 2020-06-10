from services.wrapper import Wrapper
from api.open_zaak.case_object.services import CaseObjectService

class CaseObject(Wrapper):
    fields = ('uuid', 'url', 'zaak', 'zaakUuid', 'object', 'objectType')
    service = CaseObjectService

    def __init__(self, data):
        super().__init__(data)
        self.zaakUuid = self.zaak.split('/')[-1]