from apps.open_zaak.state_type.services import LegacyStateTypeService
from services.wrapper import Wrapper


class LegacyStateType(Wrapper):
    fields = ("uuid", "url", "statustekst", "zaaktype", "omschrijving", "volgnummer")
    service = LegacyStateTypeService

    def __init__(self, data):
        super().__init__(data)
        self.uuid = self.url.split("/")[-1]
