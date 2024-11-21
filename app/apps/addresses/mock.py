def mock_do_bag_search_pdok_by_bag_id_result():
    return {
        "response": {
            "numFound": 1,
            "start": 0,
            "maxScore": 7.2593327,
            "numFoundExact": True,
            "docs": [
                {
                    "bron": "BAG",
                    "woonplaatscode": "3594",
                    "type": "adres",
                    "woonplaatsnaam": "Amsterdam",
                    "wijkcode": "WK0363AF",
                    "huis_nlt": "1",
                    "openbareruimtetype": "Weg",
                    "buurtnaam": "Waterloopleinbuurt",
                    "gemeentecode": "0363",
                    "rdf_seealso": "http://bag.basisregistraties.overheid.nl/bag/id/nummeraanduiding/0363200012145295",
                    "weergavenaam": "Amstel 1, 1011PN Amsterdam",
                    "suggest": [
                        "Amstel 1, 1011PN Amsterdam",
                        "Amstel 1, 1011 PN Amsterdam",
                    ],
                    "adrestype": "hoofdadres",
                    "straatnaam_verkort": "Amstel",
                    "id": "adr-9c02454e0f09cd9347aeb11cc03c9fb7",
                    "gekoppeld_perceel": ["ASD12-P-3514"],
                    "gemeentenaam": "Amsterdam",
                    "buurtcode": "BU0363AF09",
                    "wijknaam": "Nieuwmarkt/Lastage",
                    "identificatie": "0363010012143319-0363200012145295",
                    "openbareruimte_id": "0363300000002701",
                    "waterschapsnaam": "Waterschap Amstel, Gooi en Vecht",
                    "provinciecode": "PV27",
                    "postcode": "1011PN",
                    "provincienaam": "Noord-Holland",
                    "centroide_ll": "POINT(4.90016547 52.3676456)",
                    "geometrie_ll": "POINT(4.90016547 52.3676456)",
                    "nummeraanduiding_id": "0363200012145295",
                    "waterschapscode": "11",
                    "adresseerbaarobject_id": "0363010012143319",
                    "huisnummer": 1,
                    "provincieafkorting": "NH",
                    "geometrie_rd": "POINT(121828.874 486751.728)",
                    "centroide_rd": "POINT(121828.874 486751.728)",
                    "straatnaam": "Amstel",
                    "shards": "bag",
                    "_version_": 1816306460560195585,
                    "typesortering": 4.0,
                    "sortering": 1.0,
                    "shard": "bag",
                }
            ],
        }
    }


def mock_get_bag_identificatie_and_stadsdeel_result_without_stadsdeel():
    return {
        "_embedded": {
            "adresseerbareobjecten": [
                {
                    "huisnummer": 42,
                    "identificatie": "123456789"
                    # No "gebiedenStadsdeelNaam" key
                }
            ]
        }
    }


def mock_get_bag_identificatie_and_stadsdeel_result():
    return {
        "_embedded": {
            "adresseerbareobjecten": [
                {
                    "identificatie": "123456789",
                    "huisnummer": 42,
                    "gebiedenStadsdeelNaam": "Zuidoost",
                }
            ]
        }
    }
