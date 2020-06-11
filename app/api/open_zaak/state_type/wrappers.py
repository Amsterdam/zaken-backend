from services.wrapper import Wrapper
from api.open_zaak.state_type.services import StateTypeService

class StateType(Wrapper):
    fields = ('uuid', 'url', 'statustekst', 'zaaktype', 'omschrijving', 'volgnummer')
    service = StateTypeService

    def __init__(self, data):
        super().__init__(data)
        self.uuid = self.url.split('/')[-1]