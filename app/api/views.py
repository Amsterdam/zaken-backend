from django.http import HttpResponseBadRequest
from rest_framework.response import Response
from rest_framework.exceptions import APIException

def retrieve_helper(self, uuid):
    try:
        object = self.data_wrapper.retrieve(uuid)
        serializer = self.serializer_class(object)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'message': 'Could not retrieve object', 'error': str(e)},
            status=HttpResponseBadRequest.status_code
        )

def list_helper(self):
    objects = self.data_wrapper.retrieve_all()
    serializer = self.serializer_class(objects, many=True)
    return Response(serializer.data)

def create_helper(self, data):
    serializer = self.serializer_class(data=data)

    if not serializer.is_valid():
        raise APIException('Serializer error: {}'.format(serializer.errors))

    object = self.data_wrapper.create(data)
    serializer = self.serializer_class(object)
    return Response(serializer.data)

def destroy_helper(self, uuid):
    response = self.data_wrapper.destroy(uuid)
    return Response(response)

def update_helper(self, uuid, data):
    response = self.data_wrapper.update(uuid, data)
    serializer = self.serializer_class(response)
    return Response(serializer.data)