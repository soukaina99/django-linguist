# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.db.models import fields
from django.utils import six
from django.utils.encoding import force_text
from django.utils.functional import lazy

from . import settings
from .models import Translation

SUPPORTED_FIELDS = (fields.CharField, fields.TextField)


class TranslationField(object):
    """
    Translation Descriptor.
    """

    def __init__(self, identifier, field, language, *args, **kwargs):
        self.identifier = identifier
        self.field = field
        self.language = language
        self.attname = build_localized_field_name(self.field.name, language)
        self.name = self.attname
        self.verbose_name = build_localized_verbose_name(field.verbose_name, language)
        self.null = True
        self.blank = True

    def __get__(self, instance, instance_type=None):
        if instance is None:
            raise AttributeError('Can only be accessed via instance')
        translation = self.get_translation(instance)
        return translation.field_value if translation else getattr(instance, self.field.name)

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError('Can only be accessed via instance')
        translation = self.get_translation(instance)
        if translation is None:
            translation = Translation(
                identifier=self.identifier,
                object_id=instance.pk,
                language=self.language,
                field_name=self.field.name)
        translation.field_value = value
        translation.save()

    def get_translation(self, instance):
        try:
            translation = Translation.objects.get(
                identifier=self.identifier,
                object_id=instance.pk,
                language=self.language,
                field_name=self.field.name)
        except Translation.DoesNotExist:
            translation = None
        return translation


def build_localized_field_name(field_name, language):
    """
    Build localized field name from ``field_name`` and ``language``.
    """
    return '%s_%s' % (field_name, language.replace('-', '_'))


def _build_localized_verbose_name(verbose_name, language):
    """
    Build localized verbose name from ``verbose_name`` and ``language``.
    """
    return force_text('%s [%s]') % (force_text(verbose_name), language)

build_localized_verbose_name = lazy(_build_localized_verbose_name, six.text_type)


def create_translation_field(identifier, model, field_name, language):
    """
    Returns a ``TranslationField`` based on a ``field_name`` and a ``language``.
    """
    field = model._meta.get_field(field_name)
    cls_name = field.__class__.__name__
    if not isinstance(field, SUPPORTED_FIELDS):
        raise ImproperlyConfigured('%s is not supported by Linguist.' % cls_name)
    return TranslationField(
        identifier=identifier,
        field=field,
        language=language)


def add_translation_fields(translation_class):
    """
    Patches original model to provide fields for each language.
    """
    model = translation_class.model
    fields = translation_class.fields
    for field_name in fields:
        for language, name in settings.SUPPORTED_LANGUAGES:
            translation_field = create_translation_field(
                identifier=translation_class.identifier,
                model=model,
                field_name=field_name,
                language=language)
            localized_field_name = build_localized_field_name(field_name, language)
            if hasattr(model, localized_field_name):
                raise ValueError(
                    "Error adding translation field. Model '%s' already contains a field named"
                    "'%s'." % (model._meta.object_name, localized_field_name))
            model.add_to_class(localized_field_name, translation_field)