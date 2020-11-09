"""
Tests for class constraints models
"""
import datetime

from django.db import connection, models
from django.test import TestCase
from freezegun import freeze_time
from utils.class_mixins import (
    ModelEditable,
    ModelEditablelBase,
    ModelEditableTimeConstraint,
)


class ModelEditablelBaseTest(TestCase):
    @classmethod
    def setUpClass(cls):
        class SubClass(ModelEditablelBase):
            """ An example ModelEditablelBase subclass used for test purposes"""

            class Meta:
                app_label = "editable_model_base_test"

        cls.SubClass = SubClass
        with connection.schema_editor() as editor:
            editor.create_model(SubClass)

        super(ModelEditablelBaseTest, cls).setUpClass()

    def test_creation(self):
        self.SubClass.objects.create()

    # Inheriting from the ModelEditablelBase without configuration should cause all methods to fail.
    def test_is_editable_fail(self):
        sub_class_object = self.SubClass.objects.create()

        with self.assertRaises(Exception):
            sub_class_object.is_editable()

    def test_is_validate_fail(self):
        sub_class_object = self.SubClass.objects.create()

        with self.assertRaises(Exception):
            sub_class_object.validate()

    def test_delete_fail(self):
        sub_class_object = self.SubClass.objects.create()

        with self.assertRaises(Exception):
            sub_class_object.delete()

    def test_save_fail(self):
        sub_class_object = self.SubClass.objects.create()

        with self.assertRaises(Exception):
            sub_class_object.save()


class ModelEditableTest(TestCase):
    @classmethod
    def setUpClass(cls):
        class SubClass(ModelEditable):
            """ An example ModelEditable subclass used for test purposes"""

            IS_EDITABLE = True
            test_boolean = models.BooleanField(default=False)

            class Meta:
                app_label = "editable_model_test"

        cls.SubClass = SubClass
        with connection.schema_editor() as editor:
            editor.create_model(SubClass)

        super(ModelEditableTest, cls).setUpClass()

    def test_creation(self):
        self.assertEquals(self.SubClass.objects.count(), 0)
        self.SubClass.objects.create()
        self.assertEquals(self.SubClass.objects.count(), 1)

    def test_is_editable(self):
        subclass_object = self.SubClass.objects.create()
        self.assertTrue(subclass_object.is_editable)

    def test_validate(self):
        subclass_object = self.SubClass.objects.create()
        subclass_object.validate()

    def test_save(self):
        subclass_object = self.SubClass.objects.create()
        subclass_object.save()

    def test_delete(self):
        subclass_object = self.SubClass.objects.create()
        subclass_object.delete()
        self.assertEquals(self.SubClass.objects.count(), 0)

    def test_save_modified(self):
        subclass_object = self.SubClass.objects.create()
        updated_value = not subclass_object.test_boolean
        subclass_object.test_boolean = updated_value
        subclass_object.save()

        subclass_object = self.SubClass.objects.get(id=subclass_object.id)
        self.assertEquals(subclass_object.test_boolean, updated_value)


class NonModelEditableTest(TestCase):
    @classmethod
    def setUpClass(cls):
        class SubClass(ModelEditable):
            """ An example ModelEditable subclass used for test purposes"""

            IS_EDITABLE = False
            test_boolean = models.BooleanField(default=False)

            class Meta:
                app_label = "non_editable_model_test"

        cls.SubClass = SubClass
        with connection.schema_editor() as editor:
            editor.create_model(SubClass)

        super(NonModelEditableTest, cls).setUpClass()

    def test_creation(self):
        self.assertEquals(self.SubClass.objects.count(), 0)
        self.SubClass.objects.create()
        self.assertEquals(self.SubClass.objects.count(), 1)

    def test_is_editable(self):
        subclass_object = self.SubClass.objects.create()
        self.assertFalse(subclass_object.is_editable)

    def test_validate(self):
        subclass_object = self.SubClass.objects.create()
        with self.assertRaises(Exception):
            subclass_object.validate()

    def test_save(self):
        subclass_object = self.SubClass.objects.create()
        with self.assertRaises(Exception):
            subclass_object.save()

    def test_save_not_modified(self):
        subclass_object = self.SubClass.objects.create()
        updated_value = not subclass_object.test_boolean
        subclass_object.test_boolean = updated_value

        try:
            subclass_object.save()
        except Exception:
            pass

        subclass_object = self.SubClass.objects.get(id=subclass_object.id)
        self.assertNotEqual(subclass_object.test_boolean, updated_value)

    def test_delete(self):
        subclass_object = self.SubClass.objects.create()
        with self.assertRaises(Exception):
            subclass_object.delete()


class ModelEditableTimeConstraintFailTest(TestCase):
    @classmethod
    def setUpClass(cls):
        class SubClass(ModelEditableTimeConstraint):
            """ An example ModelEditableTimeConstraint subclass used for test purposes"""

            class Meta:
                app_label = "time_constraint_model_fail_test"

        cls.SubClass = SubClass
        with connection.schema_editor() as editor:
            editor.create_model(SubClass)

        super(ModelEditableTimeConstraintFailTest, cls).setUpClass()

    def test_creation(self):
        self.assertEquals(self.SubClass.objects.count(), 0)
        self.SubClass.objects.create()
        self.assertEquals(self.SubClass.objects.count(), 1)

    def test_date_created_fail(self):
        subclass_object = self.SubClass.objects.create()
        with self.assertRaises(Exception):
            subclass_object.date_added

    def test_is_editable_error(self):
        subclass_object = self.SubClass.objects.create()
        with self.assertRaises(Exception):
            subclass_object.is_editable

    def test_validate_error(self):
        subclass_object = self.SubClass.objects.create()
        with self.assertRaises(Exception):
            subclass_object.validate()


class ModelEditableTimeConstraintTest(TestCase):
    @classmethod
    def setUpClass(cls):
        class SubClass(ModelEditableTimeConstraint):
            """ An example ModelEditableTimeConstraint subclass used for test purposes"""

            EDITABLE_TIME_IN_SECONDS = 30
            date_added = models.DateTimeField(auto_now_add=True)

            class Meta:
                app_label = "time_constraint_model_test"

        cls.SubClass = SubClass
        with connection.schema_editor() as editor:
            editor.create_model(SubClass)

        super(ModelEditableTimeConstraintTest, cls).setUpClass()

    def test_creation(self):
        self.assertEquals(self.SubClass.objects.count(), 0)
        self.SubClass.objects.create()
        self.assertEquals(self.SubClass.objects.count(), 1)

    def test_is_editable(self):
        with freeze_time("2019-12-25"):
            subclass_object = self.SubClass.objects.create()
            self.assertTrue(subclass_object.is_editable)

    def test_time_elapsed_within_constraint(self):
        with freeze_time("2019-12-25") as frozen_datetime:
            subclass_object = self.SubClass.objects.create()

            elapsed_time = datetime.timedelta(
                seconds=subclass_object.EDITABLE_TIME_IN_SECONDS / 2
            )
            frozen_datetime.tick(delta=elapsed_time)

            self.assertTrue(subclass_object.is_editable)

    def test_time_elapsed_exceeds_constraint(self):
        with freeze_time("2019-12-25") as frozen_datetime:
            subclass_object = self.SubClass.objects.create()

            elapsed_time = datetime.timedelta(
                seconds=subclass_object.EDITABLE_TIME_IN_SECONDS + 1
            )
            frozen_datetime.tick(delta=elapsed_time)

            self.assertFalse(subclass_object.is_editable)

    def test_validate_within_time_constraint(self):
        with freeze_time("2019-12-25") as frozen_datetime:
            subclass_object = self.SubClass.objects.create()

            elapsed_time = datetime.timedelta(
                seconds=subclass_object.EDITABLE_TIME_IN_SECONDS / 2
            )
            frozen_datetime.tick(delta=elapsed_time)
            subclass_object.validate()

    def test_validate_outside_time_constraint(self):
        with freeze_time("2019-12-25") as frozen_datetime:
            subclass_object = self.SubClass.objects.create()

            elapsed_time = datetime.timedelta(
                seconds=subclass_object.EDITABLE_TIME_IN_SECONDS + 1
            )
            frozen_datetime.tick(delta=elapsed_time)
            with self.assertRaises(Exception):
                subclass_object.validate()

    def test_is_editable_until_property(self):
        with freeze_time("2019-12-25"):
            subclass_object = self.SubClass.objects.create()

            editable_time = datetime.timedelta(
                seconds=subclass_object.EDITABLE_TIME_IN_SECONDS
            )
            editable_until_time = subclass_object.date_added + editable_time

            self.assertEquals(editable_until_time, subclass_object.is_editable_until)
