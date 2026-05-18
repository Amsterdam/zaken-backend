import logging

from django.db import models
from utils.api_queries_bag import (
    do_bag_search_benkagg_by_id,
    do_bag_search_pdok_by_bag_id,
)

logger = logging.getLogger(__name__)


class District(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class HousingCorporation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    bwv_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Address(models.Model):
    bag_id = models.CharField(max_length=255, null=False, unique=True)
    nummeraanduiding_id = models.CharField(max_length=16, null=True, blank=True)
    street_name = models.CharField(max_length=255, null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    suffix_letter = models.CharField(max_length=1, null=True, blank=True)
    suffix = models.CharField(max_length=4, null=True, blank=True)
    postal_code = models.CharField(max_length=7, null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    district = models.ForeignKey(
        to=District,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    housing_corporation = models.ForeignKey(
        to=HousingCorporation,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    @property
    def full_address(self) -> str:
        """
        Retrieves a string with the full address of the object.
        """
        full_address = f"{self.street_name} {self.number}"
        if self.suffix or self.suffix_letter:
            full_address = f"{full_address}-{self.suffix}{self.suffix_letter}"

        full_address = f"{full_address}, {self.postal_code}"

        return full_address

    def __str__(self):
        if self.street_name:
            return (
                f"{self.street_name}"
                f" {self.number}{self.suffix_letter}-{self.suffix},"
                f" {self.postal_code}"
            )
        return self.bag_id

    def get_or_create_by_bag_id(bag_id):
        return Address.objects.get_or_create(bag_id=bag_id)[0]

    def get_bag_address_data(self):
        bag_search_response = do_bag_search_pdok_by_bag_id(self.bag_id)
        bag_search_results = bag_search_response.get("response", {}).get("docs", [])
        if bag_search_results:
            found_bag_data = bag_search_results[0]
            self.postal_code = found_bag_data.get("postcode", "")
            self.street_name = found_bag_data.get("straatnaam", "")
            self.number = found_bag_data.get("huisnummer", "")
            self.suffix_letter = found_bag_data.get("huisletter", "")
            self.suffix = found_bag_data.get("huisnummertoevoeging", "")
            self.nummeraanduiding_id = found_bag_data.get("nummeraanduiding_id", "")
            centroid_string = found_bag_data.get("centroide_ll", None)
            centroid = self._parse_centroid(centroid_string)
            if centroid:
                self.lng = centroid[0]
                self.lat = centroid[1]

    def _parse_centroid(self, centroid):
        # Check if the string starts with 'POINT(' and ends with ')'
        if centroid.startswith("POINT(") and centroid.endswith(")"):
            # Remove the 'POINT(' at the beginning and ')' at the end
            coordinates_str = centroid[6:-1]
            # Split the string by space to get the individual numbers
            coordinates = coordinates_str.split()
            # Convert the string numbers to float and return as a list
            return [float(coordinates[0]), float(coordinates[1])]
        else:
            raise ValueError("Input string is not in the correct format.")

    def get_bag_type_and_stadsdeel(self):
        """
        Retrieves the stadsdeel and type of address by identificatie(nummeraanduiding_id).
        """

        response = do_bag_search_benkagg_by_id(self.nummeraanduiding_id)

        adresseerbareobjecten = response.get("_embedded", {}).get(
            "adresseerbareobjecten", []
        )

        # There are adresseerbareobjecten with the same bag_id. Find the best result.
        found_bag_object = next(
            (
                adresseerbareobject
                for adresseerbareobject in adresseerbareobjecten
                if adresseerbareobject.get("huisnummer", None) == self.number
            ),
            {},
        )
        # Temporarily property for type. Could be verblijfsobject (huis) or standplaats (woonboot).
        # It's not used by now, but could be useful in the future.
        self.type = found_bag_object.get("typeAdresseerbaarObjectOmschrijving")
        district_name = found_bag_object.get("gebiedenStadsdeelNaam")

        if district_name:
            self.district = District.objects.get_or_create(name=district_name)[0]

    def update_bag_data(self):
        self.get_bag_address_data()
        # Prevent a nummeraanduiding_id error while creating a case.
        try:
            self.get_bag_type_and_stadsdeel()
        except Exception as e:
            logger.error(
                f"Could not retrieve nummeraanduiding_id for bag_id:{self.bag_id}: {e}"
            )

    def update_bag_data_and_save_address(self):
        self.update_bag_data()
        self.save()

    def save(self, *args, **kwargs):
        if not self.bag_id or not self.nummeraanduiding_id:
            self.update_bag_data()
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
