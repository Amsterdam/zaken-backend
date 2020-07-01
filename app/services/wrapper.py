class Wrapper(object):
    fields = ()
    expand_fields = ()
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

    @classmethod
    def update(cls, uuid, data):
        service = cls.service()
        data = service.update(uuid, data)
        return cls(data)

    @classmethod
    def create(cls, data):
        service = cls.service()
        response = service.post(data)
        instance = cls(response)
        return instance

    @classmethod
    def expand(cls, url):
        service = cls.service()
        connection = service.__get_connection__()
        response = connection.get_url(url)        
        return response
        

    def __init__(self, data):
        if not self.fields:
            raise ValueError('No fields set')

        self.__set_data__(data)

    def __set_data__(self, data):
        for field in self.fields:
            setattr(self, field, data.get(field, None))

        for field in self.expand_fields:
          url = data.get(field, None)
          if url:   
            expand_data = self.expand(url)
          else:
            expand_data = {}
            
          setattr(self, field, expand_data)          

        if 'debug' in self.fields:
            setattr(self, 'debug', data)
