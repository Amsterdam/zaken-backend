from rest_framework import serializers

PERMIT_DEFAULT_CHOICES = ("GRANTED", "NOT_GRANTED", "UNKNOWN")


# TODO: This is currently not used. Should it be removed?
class DecosJoinObjectFieldsResponseSerializer(serializers.Serializer):
    """
    This a serializer to just check if all fields are in the response are there
    so we can safely access the data. All fields with allow_null=True are non essential
    at the time of writing
    """

    subject1 = serializers.CharField()  # "Beschrijving (postadres)"
    mark = serializers.CharField()  # "Kenmerk (Postcode/huisnr)",
    mailaddress = serializers.CharField(
        allow_null=True, allow_blank=True
    )  # "Zeeburgerdijk 55-2",
    zipcode = serializers.CharField()  # "1094AA",
    city = serializers.CharField(allow_null=True, allow_blank=True)  # "AMSTERDAM",
    phone3 = serializers.CharField()  # Verblijfsobjectidentificatie
    text11 = serializers.CharField(
        allow_null=True, allow_blank=True
    )  # Ligplaatsidentificatie
    text4 = serializers.CharField(allow_null=True, allow_blank=True)  # Soort object
    text19 = serializers.CharField(
        allow_null=True, allow_blank=True
    )  # Verblijfsobjectstatus
    num1 = serializers.IntegerField(allow_null=True)  # Oppervlakte (m2)
    text7 = serializers.CharField(allow_null=True, allow_blank=True)  # Bouwjaar
    text8 = serializers.CharField(allow_null=True, allow_blank=True)  # Straat
    initials = serializers.CharField(allow_null=True, allow_blank=True)  # Huisnr.
    phone2 = serializers.CharField(
        allow_null=True, allow_blank=True
    )  # Huisnummertoevoeging
    text3 = serializers.CharField(allow_null=True, allow_blank=True)  # Stadsdeel
    text16 = serializers.CharField(allow_null=True, allow_blank=True)  # Gebied
    text17 = serializers.CharField(allow_null=True, allow_blank=True)  # Wijk
    text18 = serializers.CharField(allow_null=True, allow_blank=True)  # Buurt
    text21 = serializers.CharField(allow_null=True, allow_blank=True)  # Bouwblok Code
    text20 = serializers.CharField(allow_null=True, allow_blank=True)  # Pandcode
    dfunction = serializers.CharField()  # Gebruiksdoel
    text5 = serializers.CharField(allow_null=True, allow_blank=True)  # Latitude
    text6 = serializers.CharField(allow_null=True, allow_blank=True)  # Longitude
    text22 = serializers.CharField(allow_null=True, allow_blank=True)  # Ligging
    num10 = serializers.IntegerField(allow_null=True)  # WORD NIET UITGELEGD
    num11 = serializers.IntegerField(allow_null=True)  # WORD NIET UITGELEGD
    text24 = serializers.CharField(allow_null=True, allow_blank=True)  # Objecttype
    email1 = serializers.CharField(
        allow_null=True, allow_blank=True
    )  # WORD NIET UITGELEGD
    sequence = serializers.IntegerField(allow_null=True)  # Volgnummer
    itemtype_key = serializers.CharField()  # DECOS SPECIFIEK
    parentKey = serializers.CharField()  # DECOS


class DecosJoinFolderFieldsResponseSerializer(serializers.Serializer):
    bol4 = serializers.BooleanField(allow_null=True, required=False)
    bol5 = serializers.BooleanField(allow_null=True, required=False)
    bol7 = serializers.BooleanField(allow_null=True, required=False)
    company = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    date1 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    date2 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    date4 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    date5 = serializers.CharField(required=False)
    date6 = serializers.CharField(required=False)
    date7 = serializers.CharField(required=False)
    department = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    document_date = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    email1 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    email2 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    email3 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    firstname = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    dfunction = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    parentKey = serializers.CharField(allow_null=True, allow_blank=True)
    sequence = serializers.IntegerField(allow_null=True, required=False)
    itemtype_key = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    mailaddress = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    mark = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    num5 = serializers.IntegerField(allow_null=True, required=False)
    num6 = serializers.IntegerField(allow_null=True, required=False)
    phone1 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    phone3 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    processed = serializers.BooleanField(required=False)
    received_date = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    subject1 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    surname = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text2 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text6 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text7 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text8 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text9 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    title = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    zipcode = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    it_extid = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text13 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text16 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    date10 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    num7 = serializers.IntegerField(allow_null=True, required=False)
    text17 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text18 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text22 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text23 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text44 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    text45 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    date20 = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    num20 = serializers.IntegerField(allow_null=True, required=False)
    num22 = serializers.IntegerField(allow_null=True, required=False)
    itemrel_key = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )


class PermitSerializer(serializers.Serializer):
    permit_granted = serializers.ChoiceField(choices=PERMIT_DEFAULT_CHOICES)
    permit_type = serializers.CharField()
    raw_data = serializers.DictField(allow_null=True)
    details = serializers.DictField(allow_null=True)


class DecosSerializer(serializers.Serializer):
    permits = PermitSerializer(many=True)
    decos_folders = serializers.DictField(allow_null=True)


class PowerbrowserSerializer(serializers.Serializer):
    baG_ID = serializers.CharField()
    product = serializers.CharField()
    kenmerk = serializers.CharField(allow_null=True, required=False)
    muT_DAT = serializers.DateTimeField()
    status = serializers.CharField(allow_null=True, required=False)
    resultaat = serializers.CharField(allow_null=True, required=False)
    startdatum = serializers.DateTimeField()
    einddatum = serializers.DateTimeField(allow_null=True, required=False)
    vergunninghouder = serializers.CharField(allow_null=True, required=False)
    initator = serializers.CharField(allow_null=True, required=False)
    datuM_TOT = serializers.DateTimeField(allow_null=True, required=False)
