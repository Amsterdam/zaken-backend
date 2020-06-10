from wrappers.wrapper import Wrapper
from services.service_state_types import StateTypesService

class StateType(Wrapper):
    fields = ('uuid', 'url', 'statustekst')
    service = StateTypesService

    def __init__(self, data):
        super().__init__(data)
        self.uuid = self.url.split('/')[-1]