# -*- coding: utf-8 -*-
from typing import Any, Union

from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType

from telestate import TeleState

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if

__all__ = ['GotoMenuButton', 'GotoStateButton']


class Button(object):
    def to_dict(self):
        return {
            "label": self.label,
            "goto": self.goto,
            "variable": self.variable,
            "value": self.value,
        }

    # end def

    @classmethod
    def prepare_dict(cls, data):
        return dict(
            label=data['label'],
            goto=data['goto'],
            variable=data['variable'],
            value=data['value'],
        )

    # end def

    @classmethod
    def from_dict(cls, data):
        return cls(
            label=data['label'],
            goto=data['goto'],
            variable=data['variable'],
            value=data['value'],
        )
    # end def
# end class


class GotoButton(Button):
    label: str
    goto: Union[str, Any]
    variable: str
    value: JSONType

    def __init__(self, label: str, goto: Union[str, Any], variable: str = None, value: JSONType = None):
        """
        A Button navigation to a different menu, optionally setting a value.

        :param label:  The displayed text of the button
        :param goto:   Which Menu to go next.
        :param variable:  If it should store something in the state data, this is the variable name
        :param value:     If it should store something in the state data, this is the variable value
        """
        self.label = label
        self.goto = goto
        self.variable = variable
        self.value = value
    # end def

    def to_dict(self):
        return {
            "label": self.label,
            "goto": self.goto,
            "variable": self.variable,
            "value": self.value,
        }
    # end def

    @classmethod
    def prepare_dict(cls, data):
        return dict(
            label=data['label'],
            goto=data['goto'],
            variable=data['variable'],
            value=data['value'],
        )
    # end def

    @classmethod
    def from_dict(cls, data):
        data = cls.prepare_dict(data)
        return cls(
            label=data['label'],
            goto=data['goto'],
            variable=data['variable'],
            value=data['value'],
        )
    # end def
# end class


class GotoMenuButton(GotoButton):
    goto: Union[str, 'Menu']

    def __init__(self, label: str, goto: Union[str, 'Menu'], variable: str = None, value: JSONType = None):
        """
        A Button navigation to a different menu, optionally setting a value.

        :param label:  The displayed text of the button
        :param goto:   Which Menu to go next.
        :param variable:  If it should store something in the state data, this is the variable name
        :param value:     If it should store something in the state data, this is the variable value
        """
        super().__init__(label, goto, variable=variable, value=value)
    # end def

    def to_dict(self):
        return super().to_dict()
    # end def

    @classmethod
    def prepare_dict(cls, data):
        return super().prepare_dict(data)
    # end def

    @classmethod
    def from_dict(cls, data):
        data = cls.prepare_dict(data)
        return cls(
            label=data['label'],
            goto=data['goto'],
            variable=data['variable'],
            value=data['value'],
        )
    # end def
# end class


class GotoStateButton(GotoButton):
    goto: Union[str, TeleState]

    def __init__(self, label: str, goto: Union[str, TeleState], variable: str = None, value: JSONType = None):
        """
        A Button navigation to a different menu, optionally setting a value.

        :param label:  The displayed text of the button
        :param goto:   Which Menu to go next.
        :param variable:  If it should store something in the state data, this is the variable name
        :param value:     If it should store something in the state data, this is the variable value
        """
        super().__init__(label, goto, variable=variable, value=value)
    # end def

    def to_dict(self):
        return super().to_dict()
    # end def

    @classmethod
    def prepare_dict(cls, data):
        return super().prepare_dict(data)
    # end def

    @classmethod
    def from_dict(cls, data):
        data = cls.prepare_dict(data)
        return cls(
            label=data['label'],
            goto=data['goto'],
            variable=data['variable'],
            value=data['value'],
        )
    # end def
# end class


class ToggleButton(Button):
    label_on: str
    label_off: str
    variable: str
    default: bool

    def __init__(self, label_on: str, label_off: str, variable: str, default: bool):
        """
        A Button working like a checkbox, switching between `on` and `off`. Stores state in a variable.

        :param label_on:  The displayed text of the button if turned on.
        :param label_off: The displayed text of the button if turned off.
        :param variable:  Where (in the state) it should store the toggle value.
        :param default:   If it should start with `on` (`True`) or `off` (`False`).
        """
        self.label_on = label_on
        self.label_off = label_off
        self.variable = variable
        self.default = default
    # end def
# end class
