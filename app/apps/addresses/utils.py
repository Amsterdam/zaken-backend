from apps.addresses.models import Address


def search(street_name=None, postal_code=None, number=None, suffix=None):
    queryset = Address.objects.all()

    if street_name:
        # TODO: Check why lower doesn't work
        # queryset.filter(street_name__unaccent__lower__trigram_similar=street_name)
        queryset = queryset.filter(street_name__unaccent__trigram_similar=street_name)

    if postal_code:
        postal_code = postal_code.replace(" ", "").strip()
        queryset = queryset.filter(postal_code=postal_code)

    if number:
        queryset = queryset.filter(number=number)

    if suffix:
        queryset = queryset.filter(suffix=suffix)

    return queryset
