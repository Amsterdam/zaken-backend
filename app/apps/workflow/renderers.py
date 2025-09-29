"""
Custom JSON renderers for handling DotAccessDict objects in Django REST Framework.
This module contains renderers that ensure DotAccessDict objects are properly
serialized in API responses, preventing JSON serialization errors.

Note: DotAccessDict class is defined in apps.workflow.utils module.
"""

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.renderers import JSONRenderer
from rest_framework.utils.encoders import JSONEncoder


def is_dot_access_dict(obj):
    """Check if object is a DotAccessDict without importing the class directly"""
    return obj.__class__.__name__ == "DotAccessDict"


class DotAccessDictJSONEncoder(DjangoJSONEncoder):
    """
    Custom JSON encoder that handles DotAccessDict objects for Django REST Framework.
    This ensures DotAccessDict objects are properly serialized in API responses.
    """

    def default(self, obj):
        if is_dot_access_dict(obj):
            return {"value": obj.value}
        return super().default(obj)


class DRFDotAccessDictEncoder(JSONEncoder):
    """
    Custom DRF JSON encoder that handles DotAccessDict objects.
    """

    def default(self, obj):
        if is_dot_access_dict(obj):
            return {"value": obj.value}
        return super().default(obj)


class DotAccessDictJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that uses our DotAccessDict-aware encoder.
    This ensures all DotAccessDict objects are properly serialized in API responses.
    """

    encoder_class = DRFDotAccessDictEncoder
