from unittest.case import TestCase
from bson.objectid import ObjectId
from django.test import override_settings
from mock.mock import Mock, patch
from mongoengine import errors as mongoengine_errors
from django.core import exceptions as django_exceptions

from core_main_app.commons import exceptions
from core_main_app.components.template import api as template_api
from core_main_app.components.template.models import Template


class TestTemplateGet(TestCase):

    @patch('core_main_app.components.template.models.Template.get_by_id')
    def test_template_get_returns_template(self, mock_get_by_id):
        # Arrange
        mock_template_filename = "Schema"
        mock_template_content = "<schema xmlns='http://www.w3.org/2001/XMLSchema'></schema>"

        mock_template = _create_mock_template(mock_template_filename, mock_template_content)

        mock_get_by_id.return_value = mock_template

        # Act
        result = template_api.get(mock_template.id)

        # Assert
        self.assertIsInstance(result, Template)

    @patch('core_main_app.components.template.models.Template.get_by_id')
    def test_template_get_raises_exception_if_object_does_not_exist(self, mock_get_by_id):
        # Arrange
        mock_absent_id = ObjectId()
        mock_get_by_id.side_effect = mongoengine_errors.DoesNotExist

        # Act + Assert
        with self.assertRaises(mongoengine_errors.DoesNotExist):
            template_api.get(mock_absent_id)


class TestTemplateGetAllByHash(TestCase):
    @patch('core_main_app.components.template.models.Template.get_all_by_hash')
    def test_template_get_all_by_hash_contains_only_template(self, mock_get_all_by_hash):
        _generic_get_all_test(self, mock_get_all_by_hash, template_api.get_all_by_hash("fake_hash"))


class TestTemplateList(TestCase):
    @patch('core_main_app.components.template.models.Template.get_all')
    def test_template_list_contains_only_template(self, mock_get_all):
        _generic_get_all_test(self, mock_get_all, template_api.get_all())


class TestTemplateUpsert(TestCase):
    @override_settings(ROOT_URLCONF="core_main_app.urls")
    @patch('core_main_app.components.template.models.Template.save')
    def test_template_upsert_valid_returns_template(self, mock_save):
        template = _create_template(filename="name.xsd",
                                    content="<schema xmlns='http://www.w3.org/2001/XMLSchema'></schema>")

        mock_save.return_value = template
        result = template_api.upsert(template)
        self.assertIsInstance(result, Template)

    @override_settings(ROOT_URLCONF="core_main_app.urls")
    @patch('core_main_app.components.template.models.Template.save')
    def test_template_upsert_invalid_filename_raises_validation_error(self, mock_save):
        template = _create_template(filename=1,
                                    content="<schema xmlns='http://www.w3.org/2001/XMLSchema'></schema>")
        mock_save.side_effect = django_exceptions.ValidationError("")
        with self.assertRaises(django_exceptions.ValidationError):
            template_api.upsert(template)

    @patch('core_main_app.components.template.models.Template.save')
    def test_template_upsert_invalid_content_raises_xsd_error(self, mock_save):
        template = _create_template(filename="name.xsd",
                                    content="<schema></schema>")
        mock_save.return_value = None
        with self.assertRaises(exceptions.XSDError):
            template_api.upsert(template)

    @patch('core_main_app.components.template.models.Template.save')
    def test_template_upsert_no_content_raises_error(self, mock_save):
        template = _create_template(filename="name.xsd")
        mock_save.return_value = None
        with self.assertRaises(Exception):
            template_api.upsert(template)


def _generic_get_all_test(self, mock_get_all, act_function):
    # Arrange
    mock_template_filename = "Schema"
    mock_template_content = "<schema xmlns='http://www.w3.org/2001/XMLSchema'></schema>"

    mock_template_1 = _create_mock_template(mock_template_filename, mock_template_content)
    mock_template_2 = _create_mock_template(mock_template_filename, mock_template_content)
    mock_get_all.return_value = [mock_template_1, mock_template_2]

    # Act
    result = act_function

    # Assert
    self.assertTrue(all(isinstance(item, Template) for item in result))


def _create_template(filename="", content=""):
    """
    Returns a template
    :param filename:
    :param content:
    :return:
    """
    return Template(
        id=ObjectId(),
        filename=filename,
        content=content
    )


def _create_mock_template(mock_template_filename="", mock_template_content=""):
    """
    Returns a mock template
    :param mock_template_filename:
    :param mock_template_content:
    :return:
    """
    mock_template = Mock(spec=Template)
    mock_template.filename = mock_template_filename
    mock_template.content = mock_template_content
    mock_template.id = ObjectId()
    return mock_template
