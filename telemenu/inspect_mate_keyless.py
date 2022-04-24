#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
from typing import Any

from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


def is_regular_method(value: Any) -> bool:
    """Test if a value of a class is regular method.

    example::

        class MyClass(object):
            def execute(self, input_data):
                ...

    :param klass_or_instance: the class
    :param attr: attribute name
    :param value: attribute value
    """
    if inspect.isroutine(value):
        if isinstance(value, property):
            return False

        args = inspect.getfullargspec(value).args
        try:
            if args[0] == "self":
                return True
        except:
            pass

    return False


def is_class_method(value: Any) -> bool:
    """Test if a value of a class is class method.

    example::

        class MyClass(object):
            @classmethod
            def add_two(cls, a, b):
                return a + b

    :param klass_or_instance: the class
    :param attr: attribute name
    :param value: attribute value
    """
    # is a function or method
    if inspect.isroutine(value):
        if isinstance(value, property):
            return False

        args = inspect.getfullargspec(value).args
        # Can't be a regular method, must be a static method
        if len(args) == 0:
            return inspect.ismethod(value)

        # must be a regular method
        elif args[0] == "self":
            return False

        else:
            return inspect.ismethod(value)

    return False


def is_static_method(value: Any) -> bool:
    """Test if a value of a class is static method.

    example::

        class MyClass(object):
            @staticmethod
            def add_two(a, b):
                return a + b

    :param klass_or_instance: the class
    :param attr: attribute name
    :param value: attribute value
    """
    # is a function or method
    if inspect.isroutine(value):
        if isinstance(value, property):
            return False

        args = inspect.getfullargspec(value).args
        # Can't be a regular method, must be a static method
        if len(args) == 0:
            return True

        # must be a regular method
        elif args[0] == "self":
            return False

        else:
            return inspect.isfunction(value)

    return False


def is_property_method(value):
        """Test if a value of a class is @property style attribute.

        example::

            class MyClass(object):
                @property
                def value(self):
                    return 0

        :param klass_or_instance: the class
        :param attr: attribute name
        :param value: attribute value
        """
    # is a class
    # if inspect.isclass(klass_or_instance):
    #     value = getattr(klass_or_instance, attr)

        # not a function or method
        if inspect.isroutine(value):
            return False
        else:
            if isinstance(value, property):
                return True
            else:
                return False
    #
    # # is an instance
    # else:
    #     klass = klass_or_instance.__class__
    #     try:
    #         return is_property_method(klass, attr)
    #     # klass doesn't have this property
    #     except:
    #         return False
