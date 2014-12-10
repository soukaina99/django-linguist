# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .. import settings


class TranslationManager(models.Manager):

    def get_translation(self, identifier, object_id, language, field_name):
        attrs = dict(
            identifier=identifier,
            object_id=object_id,
            language=language,
            field_name=field_name)
        obj = None
        try:
            obj = self.get(**attrs)
        except self.model.DoesNotExist:
            pass
        return obj

    def set_translation(self, identifier, object_id, language, field_name, field_value):
        created = False
        attrs = dict(
            identifier=identifier,
            object_id=object_id,
            language=language,
            field_name=field_name,
            field_value=field_value)
        try:
            obj = self.get(**attrs)
        except self.model.DoesNotExist:
            obj = self.create(**attrs)
            created = True
        if obj.field_value != field_value:
            obj.field_value = field_value
            obj.save()
        return (obj, created)


@python_2_unicode_compatible
class Translation(models.Model):
    """
    A Translation.
    """
    identifier = models.CharField(
        max_length=100,
        verbose_name=_('identifier'),
        help_text=_('The registered model identifier.'))

    object_id = models.IntegerField(
        verbose_name=_('The object ID'),
        null=True,
        help_text=_('The object ID of this translation'))

    language = models.CharField(
        max_length=10,
        verbose_name=_('locale'),
        choices=settings.SUPPORTED_LANGUAGES,
        default=settings.DEFAULT_LANGUAGE,
        help_text=_('The language for this translation'))

    field_name = models.CharField(
        max_length=100,
        verbose_name=_('field name'),
        help_text=_('The model field name for this translation.'))

    field_value = models.TextField(
        verbose_name=_('field value'),
        null=True,
        help_text=_('The translated content for the field.'))

    objects = TranslationManager()

    class Meta:
        abstract = True
        app_label = 'linguist'
        verbose_name = _('translation')
        verbose_name_plural = _('translations')
        unique_together = (('identifier', 'object_id', 'language', 'field_name'),)

    def __str__(self):
        return '%s:%d:%s:%s' % (
            self.identifier,
            self.object_id,
            self.field_name,
            self.language)
