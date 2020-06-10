from services.service_state_types import StateTypesService as Service

class StateType(object):
    fields = ('pk', 'url', 'statustekst')

    @staticmethod
    def retrieve_all():
        service = Service()
        state_types_response = service.get().get('results', [])
        state_types = []

        for state_type_response in state_types_response:
            state_type = StateType(state_type_response)
            state_types.append(state_type)

        return state_types

    @staticmethod
    def retrieve(pk):
        service = Service()
        data = service.get(pk)
        return StateType(data)

    def __init__(self, data):
        for field in self.fields:
            setattr(self, field, data.get(field, None))

        self.pk = self.url.split('/')[-1]