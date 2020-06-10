class Wrapper(object):
    fields = ()
    service = None

    @classmethod
    def retrieve_all(cls):
        if not cls.service:
            raise ValueError('Service not set')

        service = cls.service()
        state_types_response = service.get().get('results', [])
        state_types = []

        for state_type_response in state_types_response:
            state_type = cls(state_type_response)
            state_types.append(state_type)

        return state_types

    @classmethod
    def retrieve(cls, uuid):
        service = cls.service()
        data = service.get(uuid)
        return cls(data)

    @classmethod
    def destroy(cls, uuid):
        service = cls.service()
        data = service.delete(uuid)
        return data

    def __init__(self, data):
        if not self.fields:
            raise ValueError('No fields set')

        self.__set_data__(data)

    def __set_data__(self, data):
        for field in self.fields:
            setattr(self, field, data.get(field, None))

    def create(self):
        raise NotImplementedError('Create method not implemented')
