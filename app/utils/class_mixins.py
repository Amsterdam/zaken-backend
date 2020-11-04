import datetime

from django.db import models


class EditableModelBase(models.Model):
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


class EditableModel(EditableModelBase):
    DEFAULT_EDITABLE = True

    class Meta:
        abstract = True

    @property
    def is_editable(self):
        return self.DEFAULT_EDITABLE

    def validate(self):
        assert self.is_editable, "Object can not be edited"


class EditableTimeConstraintModel(EditableModelBase):
    EDITABLE_TIME = None

    class Meta:
        abstract = True

    @property
    def is_editable(self):
        delta_a = datetime.datetime.now() - self.date_added
        delta_b = datetime.timedelta(seconds=self.EDITABLE_TIME)

        return delta_a <= delta_b

    def validate(self):
        assert getattr(
            self, "date_added", False
        ), "Object should have a date_created field"
        assert self.date_added, "Date added is set"
        assert self.EDITABLE_TIME, "Class configuration for EDITABLE_TIME should be set"
        assert self.is_editable, "Editable time for this object has elapsed"
