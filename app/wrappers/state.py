from wrappers.wrapper import Wrapper
from services.service_states import StatesService

class State(Wrapper):
    fields = ('uuid', 'url')
    service = StatesService

    def __init__(self, data):
        super().__init__(data)