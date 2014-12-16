# -*- coding: utf-8 -*-

def with_metaclass(meta, *bases):
    # Function from python-future and jinja2. License: BSD.
    # Allow consistent behaviours across all django versions
    # Also avoids a temporary intermediate class
    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__
        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)
    return metaclass('temporary_class', None, {})
