import datetime

from django.db import models


class ModelEditablelBase(models.Model):
    class Meta:
        abstract = True

    @property
    def is_editable(self):
        raise NotImplementedError("Function is_editable is not implemented yet")

    def validate(self):
        raise NotImplementedError("Function validate is not implemented yet")

    def delete(self, *args, **kwargs):
        self.validate()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Only validate if the object has already been created and has an ID
        if self.id:
            self.validate()
        super().save(*args, **kwargs)


class ModelEditable(ModelEditablelBase):
    IS_EDITABLE = True

    class Meta:
        abstract = True

    @property
    def is_editable(self):
        return self.IS_EDITABLE

    def validate(self):
        assert self.is_editable, "Object can not be edited"


class ModelEditableTimeConstraint(ModelEditablelBase):
    EDITABLE_TIME_IN_SECONDS = None

    class Meta:
        abstract = True

    @property
    def is_editable(self):
        time_elapsed = datetime.datetime.now() - self.date_added
        time_constraint = datetime.timedelta(seconds=self.EDITABLE_TIME_IN_SECONDS)

        return time_elapsed <= time_constraint

    @property
    def is_editable_until(self):
        time_constraint = datetime.timedelta(seconds=self.EDITABLE_TIME_IN_SECONDS)
        return self.date_added + time_constraint

    def validate(self):
        assert getattr(
            self, "date_added", False
        ), "Object should have a date_created field"
        assert self.date_added, "Date added is set"
        assert (
            self.EDITABLE_TIME_IN_SECONDS
        ), "Class configuration for EDITABLE_TIME_IN_SECONDS should be set"
        assert self.is_editable, "Editable time for this object has elapsed"
