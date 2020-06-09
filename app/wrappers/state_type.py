from services import service_state_types as service

class StateType(object):
    fields = ('pk', 'url', 'statustekst')

    @staticmethod
    def retrieve_all():
        state_types_response = service.get_state_types().get('results', [])
        state_types = []

        for state_type_response in state_types_response:
            state_type = StateType(state_type_response)
            state_types.append(state_type)

        return state_types

    @staticmethod
    def retrieve(pk):
        data = service.get_state_type(pk)
        return StateType(data)

    def __init__(self, data):
        for field in self.fields:
            setattr(self, field, data.get(field, None))

        self.pk = self.url.split('/')[-1]