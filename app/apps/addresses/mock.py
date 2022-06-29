def mock_do_bag_search_id_result():
    return {
        "_links": {
            "self": {
                "href": "https://api.data.amsterdam.nl/atlas/search/adres/?q=1100MOmo%2042&page=1"
            },
            "next": {"href": None},
            "prev": {"href": None},
        },
        "count_hits": 1,
        "count": 1,
        "results": [
            {
                "_links": {
                    "self": {
                        "href": "https://api.data.amsterdam.nl/bag/v1.1/verblijfsobject/0363010001028805/"
                    }
                },
                "type": "verblijfsobject",
                "dataset": "v11_nummeraanduiding",
                "adres": "Mockemstraat 42",
                "postcode": "1100MO",
                "straatnaam": "Mockemstraat",
                "straatnaam_no_ws": "Mockemstraat",
                "huisnummer": 42,
                "toevoeging": "42",
                "bag_huisletter": "",
                "bag_toevoeging": "",
                "woonplaats": "Amsterdam",
                "type_adres": "Hoofdadres",
                "status": "Naamgeving uitgegeven",
                "landelijk_id": "0363200000516944",
                "vbo_status": "Verblijfsobject in gebruik",
                "adresseerbaar_object_id": "0363010001028805",
                "subtype": "verblijfsobject",
                "centroid": [6.969577908893136, 52.82184218979086],
                "subtype_id": "0363010001028805",
                "_display": "Mockemstraat 42",
            }
        ],
    }


def mock_do_bag_search_id_result_without_links():
    return {
        "_links": {
            "self": {
                "href": "https://api.data.amsterdam.nl/atlas/search/adres/?q=1100MOmo%2042&page=1"
            },
            "next": {"href": None},
            "prev": {"href": None},
        },
        "count_hits": 1,
        "count": 1,
        "results": [
            {
                "type": "verblijfsobject",
                "dataset": "v11_nummeraanduiding",
                "adres": "Mockemstraat 42",
                "postcode": "1100MO",
                "straatnaam": "Mockemstraat",
                "straatnaam_no_ws": "Mockemstraat",
                "huisnummer": 42,
                "toevoeging": "42",
                "bag_huisletter": "",
                "bag_toevoeging": "",
                "woonplaats": "Amsterdam",
                "type_adres": "Hoofdadres",
                "status": "Naamgeving uitgegeven",
                "landelijk_id": "03635000650516944",
                "vbo_status": "Verblijfsobject in gebruik",
                "adresseerbaar_object_id": "03635000650516944",
                "subtype": "verblijfsobject",
                "centroid": [4.969577908893136, 52.82184218979086],
                "subtype_id": "03635000650516944",
                "_display": "Mockemstraat 42",
            }
        ],
    }


def mock_get_bag_data_result():
    return {
        "_stadsdeel": {
            "_links": {
                "self": {
                    "href": "https://api.data.amsterdam.nl/gebieden/stadsdeel/03630930000000/"
                }
            },
            "_display": "Weesp (S)",
            "code": "S",
            "naam": "Weesp",
            "dataset": "gebieden",
        },
    }


def mock_get_bag_data_result_without_stadsdeel():
    return {}
