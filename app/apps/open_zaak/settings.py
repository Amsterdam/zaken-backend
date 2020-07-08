OPEN_ZAAK = "openzaak"
# TODO: Naming of domain, sub_domains is confusing. Rewrite.
DOMAIN_CATALOGS = "catalogi"
SUB_DOMAIN_CATALOGS = "catalogussen"
SUB_DOMAIN_CASE_TYPES = "zaaktypen"
SUB_DOMAIN_STATE_TYPES = "statustypen"
SUB_DOMAIN_INFORMATION_OBJECT_TYPE = "informatieobjecttypen"
SUB_DOMAINS_CATALOGS = [
    SUB_DOMAIN_CATALOGS,
    SUB_DOMAIN_CASE_TYPES,
    SUB_DOMAIN_STATE_TYPES,
    SUB_DOMAIN_INFORMATION_OBJECT_TYPE,
]

DOMAIN_CASES = "zaken"
SUB_DOMAIN_CASES = "zaken"
SUB_DOMAIN_STATES = "statussen"
SUB_DOMAIN_CASE_OBJECTS = "zaakobjecten"
SUB_DOMAINS_CASES = [
    SUB_DOMAIN_CASES,
    SUB_DOMAIN_CASES,
    SUB_DOMAIN_CASE_OBJECTS,
    SUB_DOMAIN_STATES,
]

STATE_ADRES_GELOPEN = "Adres gelopen"
STATGE_ADRES_GELOPEN_ONGEDAAN = "Adres gelopen ongedaan gemaakt"

STATES = [
    STATE_ADRES_GELOPEN,
    STATGE_ADRES_GELOPEN_ONGEDAAN,
    "Issuemelding",
    "Onderzoek buitendienst",
    "2de Controle",
    "3de Controle",
    "Hercontrole",
    "2de hercontrole",
    "3de hercontrole",
    "Avondronde",
    "Onderzoek advertentie",
    "Weekend buitendienstonderzoek",
]

ORGANISATION_RSIN = (  # Just a randomly generated id for now (https://www.testnummers.nl/)
    "221222558"
)
ORGANISATION_NAME = "Wonen"
ORGANISATION_DOMAIN = "WONEN"
ORGANISATION_CONTACT = "Beheerder Wonen"
