from django.db import models
from utils.api_queries_bag import (
    do_bag_search_by_bag_id,
    do_bag_search_nummeraanduiding_id_by_bag_id,
    get_bag_data_by_verblijfsobject_url,
)


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
    def full_address(self):
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

    def get_or_create(bag_id):
        return Address.objects.get_or_create(bag_id=bag_id)[0]

    def search_and_set_bag_address_data(self):
        # When moving the import to the beginning of the file, a Django error follows:
        # ImproperlyConfigured: AUTH_USER_MODEL refers to model 'users.User' that has not been installed.
        from utils.exceptions import DistrictNotFoundError

        bag_search_results = []
        try:
            bag_search_response = do_bag_search_by_bag_id(self.bag_id)
            bag_search_results = bag_search_response.get("results", [])
        except Exception:
            pass

        if len(bag_search_results):
            #  A BAG search will return an array with 1 result.
            found_bag_data = bag_search_results[0]

            self.postal_code = found_bag_data.get("postcode", "")
            self.street_name = found_bag_data.get("straatnaam", "")
            self.number = found_bag_data.get("huisnummer", "")
            self.suffix_letter = found_bag_data.get("bag_huisletter", "")
            self.suffix = found_bag_data.get("bag_toevoeging", "")

            centroid = found_bag_data.get("centroid", None)
            if centroid:
                self.lng = centroid[0]
                self.lat = centroid[1]

            verblijfsobject_url = (
                found_bag_data.get("_links", {}).get("self", {}).get("href")
            )
            verblijfsobject = (
                verblijfsobject_url
                and get_bag_data_by_verblijfsobject_url(verblijfsobject_url)
            )
            district_name = verblijfsobject and verblijfsobject.get(
                "_stadsdeel", {}
            ).get("naam")
            if district_name:
                self.district = District.objects.get_or_create(name=district_name)[0]
            else:
                raise DistrictNotFoundError(
                    f"verblijfsobject_url: {verblijfsobject_url}, verblijfsobject: {verblijfsobject}"
                )

    def search_and_set_bag_nummeraanduiding_id(self):
        try:
            bag_search_nummeraanduiding_id_response = (
                do_bag_search_nummeraanduiding_id_by_bag_id(self.bag_id)
            )
            bag_search_nummeraanduidingen = bag_search_nummeraanduiding_id_response.get(
                "_embedded", {}
            ).get("nummeraanduidingen", [])
        except Exception:
            bag_search_nummeraanduidingen = []

        # If there are multiple results, find the result with the same house number.
        # TODO: What if Weesperzijde 112 and Weesperzijde 112A have the same bag_id?
        found_bag_nummeraanduiding = next(
            (
                bag_search_nummeraanduiding
                for bag_search_nummeraanduiding in bag_search_nummeraanduidingen
                if bag_search_nummeraanduiding.get("huisnummer", None) == self.number
            ),
            {},
        )

        nummeraanduiding_id = (
            found_bag_nummeraanduiding.get("_links", {})
            .get("self", {})
            .get("identificatie", "")
        )
        if nummeraanduiding_id:
            self.nummeraanduiding_id = nummeraanduiding_id

    def save(self, *args, **kwargs):
        self.search_and_set_bag_address_data()
        self.search_and_set_bag_nummeraanduiding_id()
        # TODO: If self is missing address data, don't create a case.
        return super().save(*args, **kwargs)
