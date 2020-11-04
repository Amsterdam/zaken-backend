"""
Tests for class constraints models
"""
from django.db import connection, models
from django.test import TestCase
from utils.class_mixins import EditableModel, EditableModelBase


class EditableModelBaseTest(TestCase):
    @classmethod
    def setUpClass(cls):
        class SubClass(EditableModelBase):
            """ An example EditableModelBase subclass used for test purposes"""

            class Meta:
                app_label = "editable_model_base_test"

        cls.SubClass = SubClass
        with connection.schema_editor() as editor:
            editor.create_model(SubClass)

        super(EditableModelBaseTest, cls).setUpClass()

    def test_creation(self):
        self.SubClass.objects.create()

    # Inheriting from the EditableModelBase without configuration should cause all methods to fail.
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


class EditableModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        class SubClass(EditableModel):
            """ An example EditableModel subclass used for test purposes"""

            DEFAULT_EDITABLE = True
            test_boolean = models.BooleanField(default=False)

            class Meta:
                app_label = "editable_model_test"

        cls.SubClass = SubClass
        with connection.schema_editor() as editor:
            editor.create_model(SubClass)

        super(EditableModelTest, cls).setUpClass()

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


class NonEditableModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        class SubClass(EditableModel):
            """ An example EditableModel subclass used for test purposes"""

            DEFAULT_EDITABLE = False
            test_boolean = models.BooleanField(default=False)

            class Meta:
                app_label = "non_editable_model_test"

        cls.SubClass = SubClass
        with connection.schema_editor() as editor:
            editor.create_model(SubClass)

        super(NonEditableModelTest, cls).setUpClass()

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
