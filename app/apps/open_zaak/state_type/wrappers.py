from apps.open_zaak.state_type.services import OpenZaakStateTypeService
from services.wrapper import Wrapper


class OpenZaakStateType(Wrapper):
    fields = ("uuid", "url", "statustekst", "zaaktype", "omschrijving", "volgnummer")
    service = OpenZaakStateTypeService

    def __init__(self, data):
        super().__init__(data)
        self.uuid = self.url.split("/")[-1]
