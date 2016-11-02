"""
Template models
"""

from mongoengine import *
from django_mongoengine import fields as dme_fields, Document as dme_Document


class Template(dme_Document):
    """Represents an XML schema template that defines the structure of data for curation"""
    filename = dme_fields.StringField()
    content = dme_fields.StringField()
    hash = dme_fields.StringField()
    dependencies = dme_fields.ListField(StringField(), blank=True)

    @staticmethod
    def get_all():
        """
        Return all templates
        :return:
        """
        return Template.objects()

    @staticmethod
    def get_by_id(template_id):
        """
        Return a template by its id
        :param template_id:
        :return:
        """
        return Template.objects().get(pk=str(template_id))

    @staticmethod
    def create_template(template_filename, template_content, template_hash, template_dependencies):
        """
        Create a new template
        :param template_filename:
        :param template_content:
        :param template_hash:
        :param template_dependencies:
        :return:
        """
        new_template = Template(filename=template_filename,
                                content=template_content,
                                hash=template_hash,
                                dependencies=template_dependencies).save()
        return new_template