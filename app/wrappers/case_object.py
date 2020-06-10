from wrappers.wrapper import Wrapper
from services.service_case_objects import CaseObjectsService

class CaseObject(Wrapper):
    fields = ('uuid', 'url', 'zaak', 'zaakUuid', 'object', 'objectType')
    service = CaseObjectsService

    def __init__(self, data):
        super().__init__(data)
        self.zaakUuid = self.zaak.split('/')[-1]