#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Usage:
API_KEY = "......";  from pytgbot.bot import Bot; bot = Bot(API_KEY); from luckydonaldUtils.logger import logging; logger = logging.getLogger(__name__); logging.add_colored_handler(level=logging.DEBUG);import sys;sys.path.extend(['.../r2tg/code/r2tg/telemenu_dist']);from telemenu.test import telemenu, teleflask, TestCheckboxMenu, Menu, TestTextUrlMenu, TestRadioMenu, RegisterTestMenu, Update, Message, Chat
"""
import unittest

from luckydonaldUtils.decorators import classproperty
from luckydonaldUtils.logger import logging
from telemenu.data import Data
from telemenu.menus import Menu

from .somewhere import API_KEY

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class Example(unittest.TestCase):
    """
    Example for the different types of value retrieval we support for stuff like `title` etc.
    """
    data: Data = Data()

    # noinspection PyMethodMayBeStatic
    def var0(self, data: 'Data') -> str:
        return f"(0 normal def)\nPage {data.button_page}"
    # end def

    var1 = "(1 normal str)\nPage {data.button_page}"

    var2 = lambda data: "(2 lambda)\nPage " + str(data.button_page)

    @classmethod
    def var3(cls, data: 'Data') -> str:
        return "(3 classmethod)\nPage " + str(data.button_page)
    # end def

    var4: str

    @staticmethod
    def var5(data: 'Data') -> str:
        return "(5 classmethod)\nPage {page}".format(page=data.button_page)
    # end def

    # noinspection PyPropertyDefinition
    @property
    def var6(self, data: 'Data') -> str:
        return "(6 property)\nPage " + str(data.button_page)
    # end def

    var7 = "(7 str dot format)\nPage {data.button_page}".format

    @staticmethod
    def var8(data):
        return "(8 staticmethod)\nPage " + str(data.button_page)
    # end def

    # noinspection PyPropertyDefinition
    @classproperty
    def var9(self, data: 'Data') -> str:
        return "(9 classproperty)\nPage " + str(data.button_page)
    # end def

    @classmethod
    def get_value(cls, value):
        get_value = Menu.get_value.__func__
        return get_value(cls=cls, value=value)
    # end def

    def assertEqual(self, a, b):
        assert a == b
    # end def

    def test_var0(self):
        self.__class__.data = Data()
        self.__class__.data.button_page = 123
        self.assertEqual(self.get_value(self.var0), "(0 normal def)\nPage 123")
    # end def

    def test_var1(self):
        self.__class__.data = Data()
        self.__class__.data.button_page = 123
        self.assertEqual(self.get_value(self.var1), "(1 normal str)\nPage 123")
    # end def

    @classmethod
    def test_var2(cls):
        cls.data.button_page = 123
        cls.assertEqual(cls, cls.get_value(cls.var2), "(2 lambda)\nPage 123")
    # end def

    def test_var3(self):
        self.assertEqual(self.get_value(self.var3), "(3 classmethod)\nPage 123")
    # end def

    def test_var5(self):
        self.__class__.data = Data()
        self.__class__.data.button_page = 123
        self.assertEqual(self.get_value(self.var5), "(5 classmethod)\nPage 123")
    # end def

    def test_var6(self):
        self.__class__.data = Data()
        self.__class__.data.button_page = 123
        self.assertEqual(self.__class__.get_value(self.__class__.var6), "(6 property)\nPage 123")
    # end def

    def test_var7(self):
        self.__class__.data = Data()
        self.__class__.data.button_page = 123
        self.assertEqual(self.get_value(self.var7), "(7 str dot format)\nPage 123")
    # end def

    def test_var8(self):
        self.__class__.data = Data()
        self.__class__.data.button_page = 123
        self.assertEqual(self.get_value(self.var8), "(8 staticmethod)\nPage 123")
    # end def

    def test_var9(self):
        self.__class__.data = Data()
        self.__class__.data.button_page = 123
        self.assertEqual(self.get_value(self.var9), "(9 classproperty)\nPage 123")
    # end def
# end class
