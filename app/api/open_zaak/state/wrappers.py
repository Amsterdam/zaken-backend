from services.wrapper import Wrapper
from api.open_zaak.state.services import StateService

class State(Wrapper):
    fields = ('uuid', 'url')
    service = StateService

    def __init__(self, data):
        super().__init__(data)