from django.db import models


class Address(models.Model):
    bag_id = models.CharField(max_length=255, null=False, unique=True)
    street_name = models.CharField(max_length=255, null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    suffix_letter = models.CharField(max_length=1, null=True, blank=True)
    suffix = models.CharField(max_length=4, null=True, blank=True)
    postal_code = models.CharField(max_length=7, null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    def __str__(self):
        if self.street_name:
            return (
                f"{self.street_name}"
                f" {self.number}{self.suffix_letter}{self.suffix},"
                f" {self.postal_code}"
            )
        return self.bag_id

    def get(bag_id):
        return Address.objects.get_or_create(bag_id=bag_id)[0]

    def save(self, *args, **kwargs):
        # TODO: Do a BAG request and add the remaining data
        return super().save(*args, **kwargs)


class CaseType(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)

    def get(name):
        return CaseType.objects.get_or_create(name=name)[0]

    def __str__(self):
        return self.name


class Case(models.Model):
    class Meta:
        ordering = ["start_date"]

    identification = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(auto_now=True)
    end_date = models.DateField(null=True)
    case_type = models.ForeignKey(
        to=CaseType, null=False, on_delete=models.CASCADE, related_name="cases"
    )
    address = models.ForeignKey(
        to=Address, null=False, on_delete=models.CASCADE, related_name="cases"
    )

    def get(identification):
        return Case.objects.get_or_create(identification=identification)[0]

    def __str__(self):
        if self.identification:
            return self.identification
        return ""
