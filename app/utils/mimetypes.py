import mimetypes

from django.conf import settings


def get_mimetype(extension):
    extension = extension.lower()
    mimetype = mimetypes.types_map.get(
        extension,
        settings.MIMETYPES_FALLBACK.get(
            extension.strip("."), mimetypes.types_map.get(".txt")
        ),
    )
    return mimetype
