from django.http import HttpResponseBadRequest
from rest_framework.response import Response

# Todo: cleanup helpers later
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

def list_debug(self):
    objects = self.data_wrapper.retrieve_all()
    return Response({'objects': objects})