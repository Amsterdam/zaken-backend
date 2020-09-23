from rest_framework import serializers


def get_decos_join_mock_object_fields():
    return {
        "count": 1,
        "content": [
            {
                "key": "123456678901337",
                "fields": {
                    "subject1": "Nieuwezijds Voorburgwal 147",
                    "mark": "1000AA11-8",
                    "mailaddress": "Nieuwezijds Voorburgwal 147",
                    "zipcode": "1012RJ",
                    "city": "AMSTERDAM",
                    "phone3": "0363100012167579",
                    "text11": "",
                    "text4": "woning",
                    "text19": "Verblijfsobject in gebruik",
                    "num1": 76,
                    "text7": "1655",
                    "text8": "Nieuwezijds Voorburgwal",
                    "initials": "147",
                    "phone2": "",
                    "text3": "Central",
                    "text16": "Stadsdeel Centrum",
                    "text17": "Burgwallen-Oude Zijde",
                    "text18": "BG-terrein",
                    "text21": "AQ02",
                    "text20": "0363100012167579",
                    "dfunction": "woonfunctie",
                    "text5": "4.891727",
                    "text6": "52.373148",
                    "text22": "Vrijstaand gebouw",
                    "num10": 1,
                    "num11": 4,
                    "text24": "Verblijfsobject",
                    "email1": "1012RJ147",
                    "sequence": 123456,
                    "itemtype_key": "COBJECT",
                    "parentKey": "90642DCCC2DB46469657C3D0DF0B1ED7",
                },
            }
        ],
    }


def get_decos_join_mock_folder_fields():
    return {
        "count": 1,
        "content": [
            {
                "key": "1234567891337",
                "fields": {
                    "bol4": False,
                    "bol5": False,
                    "bol7": False,
                    "company": "Woningdelen Amsterdam",
                    "date1": "2018-07-13T00:00:00",
                    "date2": "2018-09-07T00:00:00",
                    "date4": "2029-01-01T00:00:00",
                    "date5": "2018-09-28T00:00:00",
                    "date6": "2018-09-28T00:00:00",
                    "department": "Stadsdeel vergunnen",
                    "document_date": "2018-07-13T00:00:00",
                    "email1": "info@woningdelenamsterdam.nl",
                    "email2": "Blijvend bewaren",
                    "email3": (
                        "De zaak is niet verzonden naar externe applicatie(s) omdat er"
                        " geen afnemers zijn geconfigureerd voor dit zaaktype."
                    ),
                    "firstname": "Centrum",
                    "dfunction": "Verleend",
                    "parentKey": "D8D961993D7E478D9B644587822817B1",
                    "sequence": 1,
                    "itemtype_key": "FOLDER",
                    "mailaddress": "Nieuwezijds Voorburgwal 147",
                    "mark": "Z/69/1234567",
                    "num5": 4,
                    "num6": 4,
                    "phone1": "020-1234567",
                    "phone3": "10",
                    "processed": True,
                    "received_date": "2018-09-28T00:00:00",
                    "subject1": (
                        "Het verhuren van 4 kamers in Nieuwezijds Voorburgwal 147"
                    ),
                    "surname": "C.J. Los Santos",
                    "text2": "11.1.2",
                    "text6": "Nieuwezijds Voorburgwal 147 1012RJ AMSTERDAM",
                    "text7": "Indische Buurt West",
                    "text8": "Noordwestkwadrant Indische buurt Noord",
                    "text9": "Zonder loting",
                    "title": "Afgehandeld",
                    "zipcode": "1012RJ",
                    "it_extid": "RGBZ_0363aa27bf53-7b57-4e3d-b6c1-a70b5eedc393",
                    "text13": "SDC 16-18-0068",
                    "text16": "Mario, Super",
                    "date10": "2020-08-26T11:59:35",
                    "num7": 1,
                    "text17": "https://api.secure.amsterdam.nl/vergunningen/quota/kameromzettingen/dashboard/",
                    "text18": "https://api.secure.amsterdam.nl/vergunningen/quota/kameromzettingen/0363100012167579",
                    "text22": "0363100012167579",
                    "text23": "Nieuwezijds Voorburgwal 147",
                    "text44": "1012RJ147",
                    "text45": "Bed and Breakfast vergunning",
                    "date20": "2018-09-07T00:00:00",
                    "num20": 0,
                    "num22": 2018,
                    "itemrel_key": "46F0E3D8B188442F89426C59F76C1DA8",
                },
            }
        ],
    }


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
