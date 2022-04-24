#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from typing import Union, Dict, List

from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class CallbackData(object):
    type: str
    value: JSONType
    id: JSONType

    # noinspection PyShadowingBuiltins
    def __init__(self, type: str, id: JSONType = None, value: JSONType = None):
        self.type = type
        self.id = id
        self.value = value
    # end def

    def to_json_str(self):
        s = json.dumps([self.type, self.id, self.value])
        if len(s) > 64:
            raise ValueError(f'Length of serialized data is more than 64 character long: {s!r}')  # you can try setting a different menu id or similar
        # end if
        return s
    # end def

    @classmethod
    def from_json_str(cls, string):
        type, id, value = json.loads(string)
        return cls(type, id, value)
    # end def

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'type={self.type!r}, '
            f'id={self.id!r}, '
            f'value={self.value!r}'
            ')'
        )
    # end def

    __str__ = __repr__
# end class


class MenuData(object):
    """
    Class holding the data of a single menu, inside of `Data.menus[<some_name>]`.
    """
    message_id: Union[int, None]
    page: int
    data: JSONType

    def __init__(self, message_id: Union[int, None] = None, page: int = 0, data: JSONType = None):
        self.message_id = message_id
        self.page = page
        self.data = data
    # end def

    def to_dict(self) -> Dict[str, JSONType]:
        return {
            "message_id": self.message_id,
            "page": self.page,
            "data": self.data,
        }
    # end def

    @classmethod
    def from_dict(cls, data: Dict[str, JSONType]) -> 'MenuData':
        if isinstance(data, cls):
            return data
        # end if

        return cls(
            message_id=data['message_id'],
            page=data['page'],
            data=data['data'],
        )
    # end def

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'message_id={self.message_id!r}, '
            f'page={self.page!r}, '
            f'data={self.data!r}'
            ')'
        )
    # end def

    __str__ = __repr__
# end class


# TODO: there is needed a way to add your own stuff, e.g. you have other states than only menus...
class Data(object):
    menus: Dict[str, MenuData]  # keys are (menu) IDs.
    history: List[str]  # stack of IDs.
    saved_data: Dict[str, JSONType]  # keys are (menu) IDs.

    def __init__(self, menus: Dict[str, JSONType] = None, history: List[str] = None, saved_data: Dict[str, JSONType] = None):
        self.menus = {} if menus is None else menus
        self.history = [] if history is None else history
        self.saved_data = {} if saved_data is None else saved_data
    # end def

    def to_dict(self) -> Dict[str, JSONType]:
        return {
            "menus": self.menus,
            "history": self.history,
            "saved_data": self.saved_data,
        }
        # end def

    @classmethod
    def from_dict(cls, data: Dict[str, JSONType]) -> 'Data':
        if isinstance(data, cls):
            return data
        # end if

        return cls(
            menus={k: MenuData.from_dict(v) for k, v in data['menus'].items()},
            history=data['history'],
            saved_data=data['saved_data'],
        )
    # end def

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'menus={self.menus!r}, '
            f'history={self.history!r}'
            f'saved_data={self.saved_data!r}'
            ')'
        )
    # end def

    __str__ = __repr__
# end class
