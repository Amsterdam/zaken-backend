from django.conf import settings


def is_openzaak_enabled():
    if settings.OPENZAAK_ENABLED == "True" or settings.OPENZAAK_ENABLED is True:
        return True
    return False
