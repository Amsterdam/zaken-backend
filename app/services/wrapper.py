class Wrapper(object):
    fields = ()
    post_fields = ()
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
        instance = cls(data)        
        service = cls.service()
        post_data = instance.__get_post_data__()

        response = service.post(post_data)
        instance.__set_data__(response)
        return instance

    def __init__(self, data):
        if not self.fields:
            raise ValueError('No fields set')

        self.__set_data__(data)

    def __set_data__(self, data):
        for field in self.fields:
            setattr(self, field, data.get(field, None))

    def __get_post_data__(self):
        if not self.post_fields:
            raise ValueError('No post fields set')

        post_fields = {} 
        
        for field in self.post_fields:
          if field not in self.fields:
              raise ValueError('Post field {} does not exist in wrapper object fields'.format(field))
          else:
              post_fields[field] = getattr(self, field)

        return post_fields 