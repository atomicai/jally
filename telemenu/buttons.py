#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import abstractmethod
from dataclasses import dataclass
from typing import Union, Type

from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType
from pytgbot.api_types.sendable.reply_markup import InlineKeyboardButton
from typeguard import typechecked

from . import ClassValueOrCallable
from .data import Data, MenuData, CallbackData
from .menus import CallbackButtonType, Menu

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class Button(object):
    """
    Other than the menus, buttons actually are instances as you can have multiple buttons in the same menu.
    Subclassing it would be way to much work, and providing values via constructor is everything we need really.

    Therefore here any function must be working with the current instance of the button.
    """
    id: Union[str, None] = None  # None means automatic

    @abstractmethod
    def get_label(self, menu_data: MenuData):
        """ returns the text for the button """
        pass
    # end def

    @abstractmethod
    def get_inline_keyboard_button(self, menu: Type[Menu]) -> InlineKeyboardButton:
        assert issubclass(menu, Menu)
        raise NotImplementedError('Subclass must implement this.')
    # end def
# end class


@dataclass(init=False)
class ChangeMenuButton(Button):
    """
    Base class for switching menus.
    """
    label: ClassValueOrCallable[str]
    save: ClassValueOrCallable[Union[None, bool]]

    def __init__(self, label: str, save: Union[None, bool]):
        self.label = label
        self.save = save
    # end def

    @property
    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError('Subclass must implement this.')
    # end def

    @property
    @abstractmethod
    def type(self) -> str:
        raise NotImplementedError('Subclass must implement this.')
    # end def

    def get_label(self, menu_data: MenuData):
        return self.label
    # end def
# end class


@dataclass(init=False)
class GotoButton(ChangeMenuButton):
    menu: ClassValueOrCallable[Type['telemenu.menus.Menu']]
    label: ClassValueOrCallable[str]

    def __init__(self, menu: Type['telemenu.menus.Menu'], label=None, save: Union[bool, None] = None):
        if label is None:
            label = menu.title
        # end if
        super().__init__(label=label, save=save)
        self.menu = menu
    # end def

    @property
    def id(self) -> str:
        return self.menu.id
    # end def

    @property
    def type(self) -> str:
        return CallbackButtonType.GOTO
    # end def

    def get_inline_keyboard_button(self, menu: Type[Menu]) -> InlineKeyboardButton:
        assert issubclass(menu, Menu)
        return InlineKeyboardButton(
            text=self.get_label(menu.menu_data),
            callback_data=CallbackData(
                type=self.type,
                value=self.menu.id,
            ).to_json_str(),
        )
    # end def
# end class


class HistoryButton(ChangeMenuButton):
    delta: ClassValueOrCallable[str]

    @typechecked()
    def __init__(self, label: str = "Unnamed Button", delta: int = -1, save: Union[None, bool] = None):  # todo: multi-language for label
        super().__init__(label=label, save=save)
        self.delta = delta
    # end def

    def get_inline_keyboard_button(self, menu: Type[Menu]) -> InlineKeyboardButton:
        assert issubclass(menu, Menu)
        assert isinstance(self.delta, int)
        return InlineKeyboardButton(
            text=self.get_label(menu.menu_data),
            callback_data=CallbackData(
                type=self.type,
                value=self.delta,
            ).to_json_str(),
        )
    # end def
# end def


class DoneButton(HistoryButton):
    def __init__(self, label: str = "Cancel", delta: int = -1):    # todo: multi-language for label
        super().__init__(label=label, save=True)
        self.delta = delta
    # end def

    @property
    def id(self) -> str:
        return ''
    # end def

    @property
    def type(self) -> str:
        return CallbackButtonType.DONE
    # end def
# end class


@dataclass(init=False)
class BackButton(HistoryButton):
    @typechecked
    def __init__(self, label: str = "Back", delta: int = -1):    # todo: multi-language for label
        super().__init__(label=label, delta=delta, save=None)
    # end def

    @property
    def id(self) -> str:
        return ''
    # end def

    @property
    def type(self) -> str:
        return CallbackButtonType.BACK
    # end def
# end class


class CancelButton(HistoryButton):
    delta: ClassValueOrCallable[str]

    def __init__(self, label: str = "Cancel", delta: int = -1):    # todo: multi-language for label
        super().__init__(label=label, save=False)
        self.delta = delta
    # end def

    @property
    def id(self) -> str:
        return ''
    # end def

    @property
    def type(self) -> str:
        return CallbackButtonType.CANCEL
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class SelectableButton(Button):
    STATE_EMOJIS = {True: '1️⃣', False: '🅾️'}
    title: str
    value: JSONType
    default_selected: bool

    def __init__(
        self,
        title,
        value: JSONType,
        default_selected: bool = False
    ):
        self.title = title
        self.value = value
        self.default_selected = default_selected
    # end def

    @abstractmethod
    def get_selected(self, menu_data: MenuData) -> bool:
        pass
    # end def

    def get_label(self, menu_data: MenuData):
        """ returns the text for the button """
        return self.STATE_EMOJIS[self.get_selected(menu_data)] + " " + self.title
    # end def

    def get_inline_keyboard_button(self, menu: Type[Menu]) -> InlineKeyboardButton:
        assert issubclass(menu, Menu)
        return InlineKeyboardButton(
            text=self.get_label(menu.menu_data),
            callback_data=CallbackData(
                type=self.type,
                value=self.value,
            ).to_json_str()
        )
    # end def

    @property
    @abstractmethod
    def type(self) -> str:
        raise NotADirectoryError('Subclasses must implement this')
    # end def
# end class


class CheckboxButton(SelectableButton):
    STATE_EMOJIS = {True: "✅", False: "❌"}

    def get_selected(self, menu_data: MenuData) -> bool:
        if (
            menu_data.data and
            self.value in menu_data.data and
            isinstance(menu_data.data, dict) and
            isinstance(menu_data.data[self.value], bool)
        ):
            return menu_data.data[self.value]
        # end if
        return self.default_selected
    # end def

    @property
    def type(self) -> str:
        return CallbackButtonType.CHECKBOX
    # end def
# end class


class RadioButton(SelectableButton):
    STATE_EMOJIS = {True: "🔘", False: "⚫️"}

    def get_selected(self, menu_data: MenuData) -> bool:
        if (
            menu_data.data and
            isinstance(menu_data.data, str)
        ):
            return menu_data.data == self.value
        # end if
        return self.default_selected
    # end def

    @property
    def type(self) -> str:
        return CallbackButtonType.RADIOBUTTON
    # end def
# end class
