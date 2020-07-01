from rest_framework import serializers


class CaseSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    uuid = serializers.CharField(read_only=True)
    identificatie = serializers.CharField(read_only=True)
    omschrijving = serializers.CharField(required=True)
    toelichting = serializers.CharField(required=False)
    startdatum = serializers.DateField(required=True)
    einddatum = serializers.DateField(required=False)
    status = serializers.URLField(read_only=True)
    bronorganisatie = serializers.CharField(read_only=True)
    verantwoordelijkeOrganisatie = serializers.CharField(read_only=True)
    zaaktype = serializers.URLField(required=True)
    debug = serializers.JSONField(read_only=True)
