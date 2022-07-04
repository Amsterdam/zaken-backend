from django.db import models
from utils.api_queries_bag import do_bag_search_id, get_bag_data


class District(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class HousingCorporation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    bwv_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Address(models.Model):
    bag_id = models.CharField(max_length=255, null=False, unique=True)
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

    def get(bag_id):
        return Address.objects.get_or_create(bag_id=bag_id)[0]

    def save(self, *args, **kwargs):
        from utils.exceptions import DistrictNotFoundError

        try:
            bag_data = do_bag_search_id(self.bag_id)
            result = bag_data.get("results", [])
        except Exception:
            result = []

        if len(result):
            result = result[0]

            self.postal_code = result.get("postcode", "")
            self.street_name = result.get("straatnaam", "")
            self.number = result.get("huisnummer", "")
            self.suffix_letter = result.get("bag_huisletter", "")
            self.suffix = result.get("bag_toevoeging", "")

            centroid = result.get("centroid", None)
            if centroid:
                self.lng = centroid[0]
                self.lat = centroid[1]

            verblijfsobject_url = result.get("_links", {}).get("self", {}).get("href")
            verblijfsobject = verblijfsobject_url and get_bag_data(verblijfsobject_url)
            district_name = verblijfsobject and verblijfsobject.get(
                "_stadsdeel", {}
            ).get("naam")
            if district_name:
                self.district = District.objects.get_or_create(name=district_name)[0]
            else:
                raise DistrictNotFoundError(
                    f"verblijfsobject_url: {verblijfsobject_url}, verblijfsobject: {verblijfsobject}"
                )
        return super().save(*args, **kwargs)
