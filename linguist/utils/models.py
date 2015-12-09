# -*- coding: utf-8 -*-
from django.core import exceptions

import six

try:
    # py27 / py3 only
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module

from .. import settings


CLASS_PATH_ERROR = 'django-linguist is unable to interpret settings value for %s. '\
                   '%s should be in the form of a tupple: '\
                   '(\'path.to.models.Class\', \'app_label\').'


def load_class(class_path, setting_name=None):
    """
    Loads a class given a class_path. The setting value may be a string or a
    tuple. The setting_name parameter is only there for pretty error output, and
    therefore is optional.
    """
    if not isinstance(class_path, six.string_types):
        try:
            class_path, app_label = class_path
        except:
            if setting_name:
                raise exceptions.ImproperlyConfigured(CLASS_PATH_ERROR % (
                    setting_name, setting_name))
            else:
                raise exceptions.ImproperlyConfigured(CLASS_PATH_ERROR % (
                    'this setting', 'It'))

    try:
        class_module, class_name = class_path.rsplit('.', 1)
    except ValueError:
        if setting_name:
            txt = '%s isn\'t a valid module. Check your %s setting' % (
                class_path, setting_name)
        else:
            txt = '%s isn\'t a valid module.' % class_path
        raise exceptions.ImproperlyConfigured(txt)

    try:
        mod = import_module(class_module)
    except ImportError as e:
        if setting_name:
            txt = 'Error importing backend %s: "%s". Check your %s setting' % (
                class_module, e, setting_name)
        else:
            txt = 'Error importing backend %s: "%s".' % (class_module, e)
        raise exceptions.ImproperlyConfigured(txt)

    try:
        clazz = getattr(mod, class_name)
    except AttributeError:
        if setting_name:
            txt = ('Backend module "%s" does not define a "%s" class. Check'
                   ' your %s setting' % (class_module, class_name,
                                         setting_name))
        else:
            txt = 'Backend module "%s" does not define a "%s" class.' % (
                class_module, class_name)
        raise exceptions.ImproperlyConfigured(txt)
    return clazz


def get_model_string(model_name):
    """
    Returns the model string notation Django uses for lazily loaded ForeignKeys
    (eg 'auth.User') to prevent circular imports.
    This is needed to allow our crazy custom model usage.
    """
    setting_name = 'LINGUIST_%s_MODEL' % model_name.upper().replace('_', '')
    class_path = getattr(settings, setting_name, None)
    if not class_path:
        return 'linguist.%s' % model_name
    elif isinstance(class_path, basestring):
        parts = class_path.split('.')
        try:
            index = parts.index('models') - 1
        except ValueError:
            raise exceptions.ImproperlyConfigured(CLASS_PATH_ERROR % (
                setting_name, setting_name))
        app_label, model_name = parts[index], parts[-1]
    else:
        try:
            class_path, app_label = class_path
            model_name = class_path.split('.')[-1]
        except:
            raise exceptions.ImproperlyConfigured(CLASS_PATH_ERROR % (
                setting_name, setting_name))
    return '%s.%s' % (app_label, model_name)


def get_translation_lookup(identifier, field, value):
    """
    Mapper that takes a language field, its value and returns the
    related lookup for Translation model.
    """
    # Split by transformers
    parts = field.split('__')

    # Store transformers
    transformers = parts[1:] if len(parts) > 1 else None

    # Guess name / language (title[_fr])
    field_name = parts[0][:-3]
    language = parts[0][-2:]

    value_lookup = 'field_value' if transformers is None else 'field_value__%s' % '__'.join(transformers)

    lookup = {
        'field_name': field_name,
        'identifier': identifier,
        'language': language,
    }

    lookup[value_lookup] = value

    return lookup
