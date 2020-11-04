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
    class Meta:
        abstract = True

    @property
    def is_editable(self):
        # Do time check
        return True

    def validate(self):
        assert getattr(
            self, "date_created", False
        ), "Object should have a date_created field"
        assert (
            not self.date_created and not self.is_editable
        ), "Object can not be edited"
