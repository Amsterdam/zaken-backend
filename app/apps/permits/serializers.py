from rest_framework import serializers


class PermitCheckmarkSerializer(serializers.Serializer):
    has_b_and_b_permit = serializers.ChoiceField(choices=("True", "False", "UNKNOWN"))
    has_vacation_rental_permit = serializers.ChoiceField(
        choices=("True", "False", "UNKNOWN")
    )


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
    company = serializers.CharField(allow_null=True, allow_blank=True)
    date1 = serializers.CharField(allow_null=True, allow_blank=True)
    date2 = serializers.CharField(allow_null=True, allow_blank=True)
    date4 = serializers.CharField(allow_null=True, allow_blank=True)
    date5 = serializers.CharField()
    date6 = serializers.CharField()
    date7 = serializers.CharField(required=False)
    department = serializers.CharField(allow_null=True, allow_blank=True)
    document_date = serializers.CharField(allow_null=True, allow_blank=True)
    email1 = serializers.CharField(allow_null=True, allow_blank=True)
    email2 = serializers.CharField(allow_null=True, allow_blank=True)
    email3 = serializers.CharField(allow_null=True, allow_blank=True)
    firstname = serializers.CharField(allow_null=True, allow_blank=True)
    dfunction = serializers.CharField(allow_null=True, allow_blank=True)
    parentKey = serializers.CharField(allow_null=True, allow_blank=True)
    sequence = serializers.IntegerField(allow_null=True)
    itemtype_key = serializers.CharField(allow_null=True, allow_blank=True)
    mailaddress = serializers.CharField(allow_null=True, allow_blank=True)
    mark = serializers.CharField(allow_null=True, allow_blank=True)
    num5 = serializers.IntegerField(allow_null=True)
    num6 = serializers.IntegerField(allow_null=True)
    phone1 = serializers.CharField(allow_null=True, allow_blank=True)
    phone3 = serializers.CharField(allow_null=True, allow_blank=True)
    processed = serializers.BooleanField()
    received_date = serializers.CharField(allow_null=True, allow_blank=True)
    subject1 = serializers.CharField(allow_null=True, allow_blank=True)
    surname = serializers.CharField(allow_null=True, allow_blank=True)
    text2 = serializers.CharField(allow_null=True, allow_blank=True)
    text6 = serializers.CharField(allow_null=True, allow_blank=True)
    text7 = serializers.CharField(allow_null=True, allow_blank=True)
    text8 = serializers.CharField(allow_null=True, allow_blank=True)
    text9 = serializers.CharField(allow_null=True, allow_blank=True)
    title = serializers.CharField(allow_null=True, allow_blank=True)
    zipcode = serializers.CharField(allow_null=True, allow_blank=True)
    it_extid = serializers.CharField(allow_null=True, allow_blank=True)
    text13 = serializers.CharField(allow_null=True, allow_blank=True)
    text16 = serializers.CharField(allow_null=True, allow_blank=True)
    date10 = serializers.CharField(allow_null=True, allow_blank=True)
    num7 = serializers.IntegerField(allow_null=True)
    text17 = serializers.CharField(allow_null=True, allow_blank=True)
    text18 = serializers.CharField(allow_null=True, allow_blank=True)
    text22 = serializers.CharField(allow_null=True, allow_blank=True)
    text23 = serializers.CharField(allow_null=True, allow_blank=True)
    text44 = serializers.CharField(allow_null=True, allow_blank=True)
    text45 = serializers.CharField(allow_null=True, allow_blank=True)
    date20 = serializers.CharField(allow_null=True, allow_blank=True)
    num20 = serializers.IntegerField(allow_null=True)
    num22 = serializers.IntegerField(allow_null=True)
    itemrel_key = serializers.CharField(allow_null=True, allow_blank=True)


class DecosPermitSerializer(serializers.Serializer):
    PERMIT_B_AND_B = "BED_AND_BREAKFAST"
    PERMIT_VV = "VAKANTIEVERHUUR"
    PERMIT_UNKNOWN = "PERMIT_UNKNOWN"

    PERMITS = (
        (PERMIT_B_AND_B, "Bed and Breakfast vergunning"),
        (PERMIT_VV, "Vakantieverhuur vergunning"),
        (PERMIT_UNKNOWN, "Onbekende vergunning"),
    )
    permit_granted = serializers.BooleanField(default=False)
    permit_type = serializers.ChoiceField(choices=PERMITS, default=PERMIT_UNKNOWN)
    processed = serializers.CharField(allow_null=True, allow_blank=True)
    date_from = serializers.DateField(allow_null=True)
    date_to = serializers.DateField(allow_null=True, required=False)
    decos_join_web_url = serializers.URLField(default="https://decosdvl.amsterdam.nl")
