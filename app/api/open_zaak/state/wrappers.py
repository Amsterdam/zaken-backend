from api.open_zaak.state.services import StateService
from services.wrapper import Wrapper


class State(Wrapper):
    fields = ('uuid', 'url', 'zaak', 'statustype', 'datumStatusGezet', 'statustoelichting')
    service = StateService
