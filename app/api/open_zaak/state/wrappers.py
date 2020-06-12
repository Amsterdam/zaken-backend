from services.wrapper import Wrapper
from api.open_zaak.state.services import StateService

class State(Wrapper):
    fields = ('uuid', 'url', 'zaak', 'statustype', 'datumStatusGezet', 'statustoelichting')
    service = StateService