from apps.open_zaak.state_type.services import StateTypeService
from services.wrapper import Wrapper


class StateType(Wrapper):
    fields = ('uuid', 'url', 'statustekst', 'zaaktype', 'omschrijving', 'volgnummer')
    service = StateTypeService

    def __init__(self, data):
        super().__init__(data)
        self.uuid = self.url.split('/')[-1]
