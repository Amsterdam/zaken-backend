import mimetypes

from django.conf import settings


def get_mimetype(extension):
    mimetype = mimetypes.types_map.get(
        extension,
        settings.MIMETYPES_FALLBACK.get(
            extension.strip("."), mimetypes.types_map.get(".txt")
        ),
    )
    return mimetype
