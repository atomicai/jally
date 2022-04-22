#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
from abc import abstractmethod, ABCMeta
from html import escape
from enum import Enum
from pprint import pformat
from types import LambdaType, BuiltinFunctionType
from typing import ClassVar, Union, Type, cast, Callable, Any, List, Dict, Pattern, Tuple, Generator

from pytgbot.exceptions import TgApiServerException
from teleflask.new_messages import SendableMessageBase
from typeguard import check_type
from dataclasses import dataclass, field as dataclass_field

from luckydonaldUtils.decorators import classproperty
from luckydonaldUtils.exceptions import assert_type_or_raise
from luckydonaldUtils.typing import JSONType
from luckydonaldUtils.logger import logging

from pytgbot import Bot
from pytgbot.api_types.receivable.updates import Message, Update
from pytgbot.api_types.sendable.reply_markup import InlineKeyboardButton, ReplyMarkup, ForceReply
from pytgbot.api_types.sendable.reply_markup import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup
from teleflask import TBlueprint
from teleflask.exceptions import AbortProcessingPlease

from . import ClassValueOrCallable, OptionalClassValueOrCallable, ClassValueOrCallableList
from .data import Data, MenuData, CallbackData
from .utils import convert_to_underscore
from .machine import TeleMenuMachine, TeleMenuInstancesItem, TeleStateMachineMenuSerialisationAdapter
from .inspect_mate_keyless import is_class_method, is_regular_method, is_static_method, is_property_method

from telestate import TeleStateMachine, TeleState
from telestate.constants import KEEP_PREVIOUS

__author__ = 'luckydonald'


logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


RAISE_ERROR = object()

class CallbackButtonType(str, Enum):
    DONE = 'done'
    GOTO = 'goto'
    BACK = 'back'
    CANCEL = 'cancel'
    PAGINATION = 'pagination'
    CHECKBOX = 'checkbox'
    RADIOBUTTON = 'radiobutton'
# end class


class Menu(object, metaclass=ABCMeta):
    """
    A menu is a static construct holding all the information.
    It is static, so any method should work without having any instance.

    That is because you create a subclass for every menu you need,
    and overwrite functions and or class variables.
    That way there will only ever one 'instance' needed per class,
    and everything could be handled as singleton, which a static class already is.
    (Not doing the same mistake some other libs here (Looking angrily at you, Codeigniter))
    """
    _state_instance: ClassVar[TeleMenuInstancesItem]

    # noinspection PyMethodParameters
    @classproperty
    def data(cls: Type['Menu']) -> Union[Data, None]:
        if cls._state_instance is None:
            # we're called by the @dataclasses class inspector
            return None
        # end if
        return cls._state_instance.state.data
    # end def
    data: ClassVar[Data]
    data: Data

    @classproperty
    def menu_data(cls: Type['Menu']) -> Union[MenuData, None]:
        if cls.data is None:
            return None
        if cls.id not in cls.data.menus:
            return None
        # end if
        return cls.data.menus[cls.id]
    # end def

    # noinspection PyPropertyDefinition,PyMethodParameters
    @data.setter
    def data(cls: Type['Menu'], data: Union[Data, None]):
        cls.store_data(data)
    # end def

    @classmethod
    def store_data(cls: Type['Menu'], data: Union[Data, None]):
        assert isinstance(data, Data) or data is None
        cls._state_instance.state.data = data
    # end def

    bot: ClassVar[Bot]
    # noinspection PyMethodParameters
    @classproperty
    def bot(cls: Type['Menu']) -> Union[Bot, None]:
        if not cls._state_instance:
            return None
        # end if
        return cast(TBlueprint, cls.tblueprint).bot
    # end def

    menu_machine: ClassVar[TBlueprint]
    # noinspection PyMethodParameters
    @classproperty
    def menu_machine(cls: Type['Menu']) -> Union[TeleMenuMachine, None]:
        if not cls._state_instance:
            return None
        # end if
        return cast(TeleMenuMachine, cls._state_instance.machine)
    # end def

    state_machine: ClassVar[Union[TeleStateMachine, TeleStateMachineMenuSerialisationAdapter, None]]
    # noinspection PyMethodParameters
    @classproperty
    def state_machine(cls: Type['Menu']) -> Union[TeleStateMachine, TeleStateMachineMenuSerialisationAdapter, None]:
        if not cls._state_instance:
            return None
        # end if
        return cast(TeleMenuMachine, cls.menu_machine).states
    # end def

    tblueprint: ClassVar[TBlueprint]
    # noinspection PyMethodParameters
    @classproperty
    def tblueprint(cls: Type['Menu']) -> Union[TBlueprint, None]:
        if not cls._state_instance:
            return None
        # end if
        return cast(TeleStateMachine, cls.state_machine).blueprint
    # end def

    current_update: ClassVar[Update]

    # noinspection PyMethodParameters
    @classproperty
    def current_update(cls: Type['Menu']) -> Union[Update, None]:
        return cast(TeleState, cast(TeleStateMachine, cls._state_instance.machine).states.CURRENT).update
    # end def

    # noinspection PyMethodParameters
    @classproperty
    def id(cls: Type['Menu']) -> str:
        """
        Returns a unique name for this menu.
        Name must be capslock and otherwise only contain numbers and the underscore.

        :return: the name to use
        """
        return convert_to_underscore(cls.__name__).upper()
    # end def

    # noinspection PyMethodParameters
    @classmethod
    def get_last_menu(cls, activate: bool = False) -> Union[None, Type['Menu']]:
        """
        Returns the previous menu in the history, or None if there is none.
        :param activate: Make the last menu active, and remove it from the history.
        :return:
        """
        return cls._state_instance.machine.get_last_menu(activate=activate)
    # end def

    @classmethod
    def _activate(cls, add_history_entry: Union[bool, None] = None, update: Union[Update, None, KEEP_PREVIOUS.__class__] = KEEP_PREVIOUS):
        """
        Activates the underlying state of the menu, and copies over the data to the new state.

        :param add_history_entry: If we should add to the menu history.
                                  `None` (default): Automatically add the new menu to the history, if that's not the active menu already.
                                  `True`: Forcefully add the menu to the history, even if we are activating the menu we're already are on.
                                  `False`: Don't append to the history.
        :type  add_history_entry: bool|None

        :param update: The Telegram Update this state is based on. Default is `KEEP_PREVIOUS`,
                       so if you activate this state without specifying an different value for this,
                       the update will stay the same for the new chosen state.
        :type  update: KEEP_PREVIOUS.__class__|Update|None
        :return:
        """
        instance: TeleMenuInstancesItem = cls._state_instance
        data = cls._state_instance.machine.states.CURRENT.data
        logger.debug(f'activating menu {cls.id!r}.\nCurrent data is {data!r}, current update is {cls.current_update!r}.')
        if data is None:
            data = Data()
        # end if
        if add_history_entry is None:
            # None: Add history automatically, if we're not the active menu already, especially if the list is empty.
            add_history_entry = len(data.history) == 0 or data.history[-1] != cls.id
        # end if
        if add_history_entry:
            data.history.append(cls.id)
        # end if
        if cls.id not in data.menus:
            logger.debug('first time load of that menu, initializing data.')
            tmp_data = cls.prepare_tmp_data()
            data.menus[cls.id] = MenuData(data=tmp_data)
            data.saved_data[cls.id] = None
        # end if
        instance.state.activate(data, update=update)
    # end def

    @classmethod
    def activate(cls, add_history_entry: Union[bool, None] = None):
        """
        Activates the underlying state of the menu, and copies over the data to the new state.

        :param add_history_entry: If we should add to the menu history.
                                  `None` (default): Automatically add the new menu to the history, if that's not the active menu already.
                                  `True`: Forcefully add the menu to the history, even if we are activating the menu we're already are on.
                                  `False`: Don't append to the history.
        :type  add_history_entry: bool|None
        :return:
        """
        cls._activate(add_history_entry=add_history_entry)
    # end def

    @classmethod
    def show(cls):
        """
        Activates the menu, and sends a menu, returning the send message.
        :return:
        """
        cls.activate()
        return cls.send()
    # end def

    @classmethod
    def get_value_by_name(cls, key, default=RAISE_ERROR):
        """
        This function is able to grab any value from a menu class by property name,
        no matter if it is a string or (class-/instance-/lambda-/...) function.
        Also it will provide the `data` to that function as well.
        In case of native strings, str.format(data=data) is called as well.

        :param key: what attribute to access
        :param default: if unset (default: RAISE_ERROR) it will raise an KeyError, otherwise that default parameter is returned
        :return:
        """
        value = getattr(cls, key, default)
        if value == RAISE_ERROR:
            raise KeyError(f'Key {key!r} not found.')
        # end if
        return cls.get_value(value)
    # end def

    @classmethod
    def get_value(cls, value: Union[Callable, LambdaType, str, property, JSONType, Any]) -> Any:
        """
        This function is able to grab any value from a menu class by property name,
        no matter if it is a string or (class-/instance-/lambda-/...) function.
        Also it will provide the `data` to that function as well.
        In case of native strings, str.format(data=data) is called as well.

        :param value: The variable to resolve.
        :return:
        """

        # params = dict(state=None, user=None, chat=None)
        if isinstance(value, str):
            return value.format(data=cls.data)
        # end if
        if isinstance(value, BuiltinFunctionType):
            # let's assume you wrote `some_var = "...".format`
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                # some_var = some_function()
                return value(data=cls.data)
            elif len(sig.parameters) > 0:
                # some_var = some_function(data)
                return value(cls.data)
            # end if
            # some_var = some_function()
            return value()
        # end if
        if is_class_method(value):
            value: Callable
            # @classmethod
            # def some_func(cls, data)
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                # some_var = some_function(data=None)
                first_param: inspect.Parameter = list(sig.parameters.values())[0]
                if 'cls' in sig.parameters or isinstance(first_param.annotation, type) and issubclass(first_param.annotation, Menu):
                    return value(data=cls.data)  # value already is class.some_function, therefore cls will be filled.
                return value(data=cls.data)
            elif len(sig.parameters) == 1:
                # some_var = some_function(data)
                return value(cls.data)
            # end if
            # some_var = some_function()
            return value()
            # end if
        if is_regular_method(value):
            # def some_func(self, ...)
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                # def some_func(self, data)
                return value(self=cls, data=cls.data)
                # end if
            return value(self=cls)
        # end if
        if is_static_method(value):
            # @staticmethod
            # def some_func(...):
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                # def some_func(data)
                if 'cls' in sig.parameters:
                    return value(cls=cls, data=cls.data)
                # end if
                return value(data=cls.data)
            # end if
            if 'cls' in sig.parameters:
                return value(cls=cls)
            # end if
            return value()
        # end if
        if is_property_method(value):
            # @property
            # def some_func(self):
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                return value.fget(data=cls.data)
            # end if
            return value.fget()
        # end if
        if isinstance(value, LambdaType):
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                return value(data=cls.data)
            # end if
            return value()
        # end if

        # if all that didn't work, just return it.
        return value
    # end def

    @classmethod
    def register_state_instance(cls, instance_item):
        """
        Function to register a state.

        :param instance_item:
        :return:
        """
        cls._state_instance = instance_item
    # end def

    title: OptionalClassValueOrCallable[str]
    description: OptionalClassValueOrCallable[str]
    done: OptionalClassValueOrCallable[Union['DoneButton', 'Menu', 'GotoButton']]
    back: OptionalClassValueOrCallable[Union['BackButton', 'Menu', 'GotoButton']]
    cancel: OptionalClassValueOrCallable[Union['CancelButton', 'Menu', 'GotoButton']]

    @classmethod
    def text(cls) -> str:
        """
        This function returns the HTML formatted text for the button.
        :return:
        """
        text = ""
        title = cls.get_value(cls.title) if hasattr(cls, 'title') else None
        if title:
            do_escape: bool = bool(cls.get_value(cls.title_escape)) if hasattr(cls, 'title_escape') else True
            logger.debug('title has escape: {}'.format(do_escape))
            if do_escape:
                text += f"<b>{escape(title)}</b>\n"
            else:
                text += str(title) + "\n"
            # end if
        # end if
        description = cls.get_value(cls.description) if hasattr(cls, 'description') else False
        if description:
            do_escape: bool = bool(cls.get_value(cls.description_escape)) if hasattr(cls, 'description_escape') else True
            logger.debug('description has escape: {}'.format(do_escape))
            if do_escape:
                text += f"{escape(description)}\n"
            else:
                text += str(description) + "\n"
            # end if
        # end if

        value = cls.get_value(cls.value) if hasattr(cls, 'value') else None
        if value:
            do_escape: bool = bool(cls.get_value(cls.value_escape)) if hasattr(cls, 'value_escape') else True
            logger.debug('value has escape: {}'.format(do_escape))
            if do_escape:
                text += f"<i>{escape(value)}</i>\n"
            else:
                text += str(value) + "\n"
            # end if
        # end if
        return text
    # end def

    @classmethod
    @abstractmethod
    def reply_markup(cls) -> Union[None, ReplyMarkup]:
        """
        This funktion is responsible for returning the `reply_markup` parameter,
        as used in pytgbot.Bot.send_message and other send_* methods.
        """
        pass
    # end def

    @classmethod
    #@abstractmethod
    def send(cls) -> Message:
        """
        This function sends a message to the state's chat and stores the information about it in the current update.

        :return:
        """
        bot: Bot = cast(Bot, cls.bot)
        assert_type_or_raise(bot, Bot, parameter_name='bot')

        text: str
        text = cls.get_value(cls.text)

        reply_markup: Union[None, ReplyMarkup, ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        reply_markup = cls.get_value(cls.reply_markup)

        chat_id: Union[int, None]
        user_id: Union[int, None]
        chat_id, user_id = TeleStateMachine.update_get_chat_and_user(cls.current_update)

        reply_chat: Union[int, None]
        reply_msg: Union[int, None]
        reply_chat, reply_msg = TeleStateMachine.msg_get_reply_params(cls.current_update)
        assert_type_or_raise(chat_id, int, parameter_name='chat_id')

        msg = bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='html',
            disable_web_page_preview=True,
            disable_notification=False,
            reply_to_message_id=reply_msg,
            reply_markup=reply_markup,
        )
        # If a new message is to be posted, the new message_id must be tracked.
        cast(MenuData, cls.menu_data).message_id = msg.message_id
        return msg
    # end def

    @classmethod
    def refresh(cls, done: bool = False) -> Message:
        """
        Edit the posted message to reflect new state, or post a new one if needed.
        To find the message to edit it uses the last saved state message_id as be found in `menu.data.menus[menu.id].message_id`.

        # TODO: If a new message is to be posted newly, the new message_id must be tracked,
        # TODO: and maybe also the old keyboard removed.
        # TODO: maybe menus should offer a 'def done_text_addendum(cls) -> str' function for `done=True`.

        :param done: Set to true if this message is not the current any longer.
                     Used to e.g. include the selection in the message when the new menu is opened below.
        :return:
        """
        bot: Bot = cast(Bot, cls.bot)
        assert_type_or_raise(bot, Bot, parameter_name='bot')

        text: str
        text = cls.get_value(cls.text)

        reply_markup: Union[None, ReplyMarkup, ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        reply_markup = cls.get_value(cls.reply_markup) if not done else None

        message_id: int = cast(MenuData, cls.menu_data).message_id
        assert message_id is not None

        chat_id: Union[int, None]
        user_id: Union[int, None]
        chat_id, user_id = TeleStateMachine.update_get_chat_and_user(cls.current_update)
        assert_type_or_raise(chat_id, int, parameter_name='chat_id')

        # reply_chat, reply_msg = TeleStateMachine.msg_get_reply_params(cls.current_update)
        logger.debug(
            f'Editing the message... (\n'
            f' text={text!r},\n'
            f' chat_id={chat_id!r},\n'
            f' message_id={message_id!r},\n'
            f' parse_mode={"html"!r},\n'
            f' disable_web_page_preview={True!r},\n'
            f' reply_markup={reply_markup!r},\n'
            ')'
        )
        msg = bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            parse_mode='html',
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )
        return msg
    # end def

    @classmethod
    def switch_to_menu(cls, menu):
        """
        Loads a new menu,
        making sure it does edit where possible,
        or close the current message and reopen a new one if not.
        :param menu:
        :return:
        """
        # it can't edit from an existing SendMenu and can't edit to it SendMenu either,
        # because you can't remove or add a ForceReply.
        can_edit = not issubclass(cls, SendMenu) and not issubclass(menu, SendMenu)
        # end if
        if can_edit:
            menu.activate()
            menu.refresh(done=False)
        else:
            try:
                cls.refresh(done=True)
            except TgApiServerException as e:
                logger.debug('Could not refresh menu.', exc_info=True)
            # end if
            menu.activate()
            menu.send()
        # end if
    # end def


    @classmethod
    def switch_history(cls, delta: int, save: Union[None, bool]):
        """
        Moves in the history.

        Currently only going backwards is supported (negative delta).
        """
        assert delta < 0
        delta = abs(delta)
        menu: Union[None, Type[Menu]] = None
        for i in range(delta):
            menu = menu if menu else cls
            # BACK: do nothing, CANCEL: delete, DONE: keep & copy
            if isinstance(save, bool) and not save:
                # delete old data
                menu.delete_tmp_data()
            if isinstance(save, bool) and save:
                # store old data
                menu.save_data()
            # end if
            menu = cls.get_last_menu(activate=True)
        # end for
        if menu:
            cls.switch_to_menu(menu)
        # end if
    # end def


    @classmethod
    def save_data(cls):
        """ Saves the current state's data, for example used on 'Done'. """
        cast(Data, cls.data).saved_data[cls.id] = cast(Data, cls.data).menus[cls.id].data
    # end def

    @classmethod
    def delete_tmp_data(cls):
        """ Deletes the current state's data, for example used on 'Cancel'. """
        del cast(Data, cls.data).menus[cls.id]
    # end def

    @classproperty
    @abstractmethod
    def tmp_data_access(cls):
        return cast(MenuData, cls.menu_data).data
    # end def

    @tmp_data_access.setter
    @abstractmethod
    def tmp_data_access_setter(cls, data):
        cast(MenuData, cls.menu_data).data = data
    # end def

    @classproperty
    @abstractmethod
    def saved_data_access(cls):
        return cast(Data, cls.data).saved_data[cls.id]
    # end def

    @saved_data_access.setter
    @abstractmethod
    def saved_data_access_setter(cls, data):
        cast(Data, cls.data).saved_data[cls.id] = data
    # end def

    @classmethod
    @abstractmethod
    def prepare_tmp_data(cls):
        raise NotImplementedError(f'Subclasses {cls.__name__} should implement this.')
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class ButtonMenu(Menu):
    """
    Subclass for everything with inline Keyboard
    """

    @TeleMenuMachine.mark_for_register.on_update('callback_query')  # yes, this must be under the classmethod!
    @classmethod
    def _on_callback_query(cls, update: Update):
        """
        Handles callback data of the menu buttons.
        This is an internal method, you should customize `cls.process_callback_data` instead.
        :param update:
        :return:
        """
        logger.debug(f'Got called for update: {cls!r}, {update!r}')
        assert isinstance(update, Update)
        # Update.callback_query
        # CallbackData(
        #     type=CallbackButtonType.PAGINATION,
        #     value=data.page - 1,
        # ).to_json_str(),
        data = CallbackData.from_json_str(update.callback_query.data)
        bot: Bot = cast(Bot, cls.bot)
        logger.debug('processing callback query with data: {data!r}.')
        try:
            cls.process_callback_data(data)
            bot.answer_callback_query(update.callback_query.id, text='Could not find the action you have clicked.', show_alert=True)
            raise NotImplementedError(f'The data {data!r} was not handled.')
        except AbortProcessingPlease as e:
            assert_type_or_raise(e.return_value, str, None, parameter_name='AbortProcessingPlease.return_value')
            if e.return_value:
                bot.answer_callback_query(update.callback_query.id, text=e.return_value, show_alert=True)
            else:
                bot.answer_callback_query(update.callback_query.id, text='OK', show_alert=False)  # TODO: l18n
            # end if
        except Exception as e:
            bot.answer_callback_query(update.callback_query.id, text='Something did fail. Sorry.', show_alert=True)
            logger.exception('Processing the callback query callback failed.')
        # end try
    # end def

    @classmethod
    def process_callback_data(cls, data: CallbackData) -> None:
        """
        Processes the callback data.
        Raises an `AbortProcessingPlease` if it did find something valid to process.

        Here specifically, the callbacks with type `CallbackButtonType.PAGINATION` are handled.

        :param data: the callback data to handle
        :raises AbortProcessingPlease: If we have handled it.
        :return: None
        """
        logger.debug(f'{cls.__name__} got callback data: {data!r}')

        # check if we need to do pagination
        if data.type == CallbackButtonType.PAGINATION:
            assert isinstance(cls.menu_data, MenuData)
            assert isinstance(data.value, int)
            cls.menu_data.page = data.value
            cls.refresh(done=False)
            raise AbortProcessingPlease()  # basically a subclass callstack safe "return None"
        # end if
        if data.type in (CallbackButtonType.BACK, CallbackButtonType.DONE, CallbackButtonType.CANCEL):
            save = {
                CallbackButtonType.BACK: None,
                CallbackButtonType.DONE: True,
                CallbackButtonType.CANCEL: False,
            }[data.type]
            cls.switch_history(delta=data.value, save=save)
            raise AbortProcessingPlease()
        # end if
    # end def

    @classmethod
    def reply_markup(cls) -> Union[None, ReplyMarkup]:
        """
        Generate an inline markup for the message to contain.
        :return:
        """
        return cls.get_keyboard()
    # end def

    @classmethod
    @abstractmethod
    def get_buttons(cls) -> List['Button']:
        """
        Retrieval of menu specific buttons.
        This is just a single list of buttons, which will be formatted later.
        Also pagination and back/cancel stuff will be added later as well.

        :return:
        """
        pass
    # end def

    @classmethod
    def get_keyboard(cls) -> Union[ReplyMarkup, None]:
        """
        This is the method which is responsible for returning a ReplyMarkup (e.g. InlineKeyboardMarkup) or None.
        Basically we need to return something which can be used in the `bot.send_message(..., reply_markup=...)` parameter.

        :return:
        """
        from .buttons import BackButton, CancelButton, DoneButton, HistoryButton, Button

        content_buttons = []
        history_buttons = []  # Back, Cancel, Done
        buttons = cls.get_buttons()
        for i, button in enumerate(buttons):
            assert_type_or_raise(button, Button, parameter_name=f'buttons[{i}]')
            if isinstance(button, HistoryButton):
                history_buttons.append(button)
            else:
                content_buttons.append(button)
            # end if
        # end for
        del button, buttons

        extra_button = cls.get_cancel_button()
        if extra_button:
            history_buttons.append(extra_button)
        # end if
        extra_button = cls.get_back_button()
        if extra_button:
            history_buttons.append(extra_button)
        # end if
        extra_button = cls.get_done_button()
        if extra_button:
            history_buttons.append(extra_button)
        # end if

        pages = (len(content_buttons) // 10) + 1
        data: MenuData = cls.menu_data
        page = data.page if data else 0

        if page >= pages:
            page = pages - 1
        # end def
        if page < 0:
            page = 0
        # end def

        offset = page * 10
        content_buttons = content_buttons[offset: offset + 10]

        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="<",
                    callback_data=CallbackData(
                        type=CallbackButtonType.PAGINATION,
                        value=page - 1,
                    ).to_json_str(),
                )
            )
        # end if
        for i in range(max(page - 2, 0), page):
            pagination_buttons.append(
                    InlineKeyboardButton(
                    text=str(i),
                    callback_data=CallbackData(
                        type=CallbackButtonType.PAGINATION,
                        value=i,
                    ).to_json_str()
                )
            )
        # end def
        for i in range(page + 1, min(page + 3, pages)):
            pagination_buttons.append(
                InlineKeyboardButton(
                    text=str(i),
                    callback_data=CallbackData(
                        type=CallbackButtonType.PAGINATION,
                        value=i,
                    ).to_json_str()
                )
            )
        # end def
        if page < pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text=">",
                    callback_data=CallbackData(
                        type=CallbackButtonType.PAGINATION,
                        value=page + 1,
                    ).to_json_str()
                )
            )
        # end if

        # split the content buttons over two rows.
        button_rows = []
        for i, button in enumerate(content_buttons):
            if i % 2 == 0:
                button_rows.append([])  # add list
            # end if
            if isinstance(button, Button):
                button = button.get_inline_keyboard_button(cls)
            # end if
            button_rows[-1].append(button)
        # end for

        if pagination_buttons:
            row = []
            check_type('pagination_buttons', pagination_buttons, List[InlineKeyboardButton])
            for button in pagination_buttons:
                if isinstance(button, Button):
                    button = button.get_inline_keyboard_button(cls)
                # end if
                assert isinstance(button, InlineKeyboardButton)
                row.append(button)
            # end for
            button_rows.append(row)
        # end def

        # add back/cancel/done as an extra row
        if history_buttons:
            row = []
            check_type('history_buttons', history_buttons, List[Button])
            for button in history_buttons:
                assert isinstance(button, Button)
                row.append(button.get_inline_keyboard_button(cls))
            # end for
            button_rows.append(row)
        # end if
        logger.debug('got the button rows: {}'.format(pformat(button_rows)))
        check_type('button_rows', button_rows, List[List[InlineKeyboardButton]])
        return InlineKeyboardMarkup(inline_keyboard=button_rows)
    # end def

    @classmethod
    def get_done_button(cls) -> Union[InlineKeyboardButton, None]:
        from .buttons import DoneButton, GotoButton, ChangeMenuButton
        DONE_BUTTON_TYPE = Union[None, str, Type[Menu], DoneButton, GotoButton, ]
        done: DONE_BUTTON_TYPE = cls.get_value(cls.done) if hasattr(cls, 'done') else None
        check_type('done', done, DONE_BUTTON_TYPE)

        if done is None:
            return None  # no button
        # end if
        if isinstance(done, str):
            done = DoneButton(label=done)
        # end if
        if inspect.isclass(done) and issubclass(done, Menu):
            done = GotoButton(menu=done, save=True)
        # end if
        if isinstance(done, ChangeMenuButton):
            assert done.save == True
        # end if
        check_type('done', done, Union[GotoButton, DoneButton])
        return done
    # end def

    @classmethod
    def get_back_button(cls) -> Union['HistoryButton', None]:
        from .buttons import GotoButton, BackButton, CancelButton, ChangeMenuButton
        BACK_BUTTON_TYPE = Union[None, str, Type[Menu], BackButton, GotoButton]

        back: BACK_BUTTON_TYPE = cls.get_value(cls.back) if hasattr(cls, 'back') else None
        check_type('back', back, BACK_BUTTON_TYPE)
        if back is None:
            return None  # no button
        # end if
        if isinstance(back, str):
            back = BackButton(label=back)
        # end if
        if inspect.isclass(back) and issubclass(back, Menu):
            back = GotoButton(menu=back, save=True)
        # end if
        if isinstance(back, ChangeMenuButton):
            assert back.save is None
        # end if
        check_type('back', back, Union[BackButton, GotoButton, CancelButton])
        return back
    # end def

    @classmethod
    def get_cancel_button(cls) -> Union[InlineKeyboardButton, None]:
        from .buttons import GotoButton, BackButton, CancelButton, ChangeMenuButton
        CANCEL_BUTTON_TYPE = Union[None, str, Type[Menu], BackButton, GotoButton, CancelButton]

        cancel: CANCEL_BUTTON_TYPE = cls.get_value(cls.cancel) if hasattr(cls, 'cancel') else None
        check_type('cancel', cancel, CANCEL_BUTTON_TYPE)
        if cancel is None:
            return None  # no button
        # end if
        if isinstance(cancel, str):
            cancel = CancelButton(label=cancel)
        # end if
        if inspect.isclass(cancel) and issubclass(cancel, Menu):
            cancel = GotoButton(menu=cancel, save=True)
        # end if
        if isinstance(cancel, ChangeMenuButton):
            assert cancel.save == False
        # end if
        cancel: Union[BackButton, GotoMenu, CancelButton]
        check_type('cancel', cancel, Union[BackButton, GotoButton, CancelButton])
        return cancel
    # end def

    @classmethod
    @abstractmethod
    def on_inline_query(cls, update: Update):
        """
        Processes the inline_query update, to do the button clicky thingy.

        :param update:
        :return:
        """
        pass
    # end def

    @classproperty
    @abstractmethod
    def value(cls) -> Union[str, None]:
        raise NotImplementedError(f'Subclass {cls.__name__} must implement this.')
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class GotoMenu(ButtonMenu):
    menus: ClassValueOrCallableList[Union['GotoButton', Type['Menu']]]

    @classmethod
    @abstractmethod
    def menus(cls) -> List[Union['GotoButton', Type['Menu']]]:
        pass
    # end def

    @classmethod
    def get_buttons(cls) -> Generator['Button', None, None]:
        from .buttons import ChangeMenuButton, GotoButton
        menus: List[Union[ChangeMenuButton, Type[Menu]]] = cls.get_value(cls.menus) if hasattr(cls, 'menus') else []
        check_type(argname='cls.menus', value=menus, expected_type=List[Union[ChangeMenuButton, Type[Menu]]])
        for menu in menus:
            if inspect.isclass(menu) and issubclass(menu, Menu):
                yield GotoButton(menu=menu)
                continue
            # end if
            assert isinstance(menu, ChangeMenuButton)
            yield menu
        # end for
    # end def

    @classmethod
    def prepare_tmp_data(cls):
        """
        Prepares the data to initialize with on the first load.
        :return:
        """
        return None
    # end def

    @classmethod
    def process_callback_data(cls, data: CallbackData):
        """
        Processes the callback data.
        Raises an `AbortProcessingPlease` if it did find something valid to process.

        Here specifically, the callbacks with type `CallbackButtonType.GOTO` are handled.

        :param data: the callback data to handle
        :raises AbortProcessingPlease: If we have handled it.
        :return: None
        """
        logger.debug(f'{cls.__name__} got callback data: {data!r}')

        if data.type == CallbackButtonType.GOTO:
            menu_id = data.value
            menu: Menu = cast(TeleMenuInstancesItem, cls._state_instance.machine.instances[menu_id]).menu
            cls.switch_to_menu(menu)
            raise AbortProcessingPlease()
        # end if
        super().process_callback_data(data)
    # end def

    @classproperty
    def value(cls) -> Union[str, None]:
        return None
    # end def
# end class


# @dataclass(init=False, eq=False, repr=True)
class SelectableMenu(ButtonMenu):
    """
    Menu for the option to choose one from many.
    """
    MENU_TYPE = 'selectable_menu'  # used for CallbackData.type

    title: str

    # noinspection PyShadowingBuiltins
    @classmethod
    def _get_our_buttons(cls, key='selectable_buttons') -> List['Button']:
        """
        Generate InlineKeyboardButton from the buttons.

        Yay, D.R.Y. code.

        :param key: the name of the class variable containing the list of selectable buttons.
        :return: list of inline buttons
        """
        from .buttons import SelectableButton, CheckboxButton, RadioButton

        buttons: List[
            Union[
                SelectableButton,
                CheckboxButton,
                RadioButton
            ]
        ] = cls.get_value_by_name(key)
        return buttons
    # end def

    @classmethod
    @abstractmethod
    def get_buttons(cls) -> List[InlineKeyboardButton]:
        pass
    # end def

    @classproperty
    @abstractmethod
    def value(cls) -> Union[str, None]:
        return f'Subclass {cls.__name__} must implement `@classproperty` `value(cls)`.'
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class CheckboxMenu(SelectableMenu):
    """
    Data storage is an dict with the checkbox values as keys, and bool as values.
    """
    MENU_TYPE = 'checkbox'  # used for CallbackData.type
    DATA_TYPE = Dict[str, bool]  # key is the button's id

    tmp_data_access: ClassVar[Union[None, DATA_TYPE]]
    saved_data_access: ClassVar[Union[None, DATA_TYPE]]

    checkboxes: ClassValueOrCallable['CheckboxButton']

    @classmethod
    def get_buttons(cls) -> List['Button']:
        return cls._get_our_buttons(key='checkboxes')
    # end def

    @classmethod
    def prepare_tmp_data(cls):
        """
        Prepares the data to initialize with on the first load.
        :return:
        """
        from .buttons import CheckboxButton
        logger.debug(f'preparing tmp data for class {cls.__name__}.')
        button: CheckboxButton
        data = {}
        for button in cls.get_value(cls.checkboxes):
            data[button.value] = button.default_selected
        # end for
        logger.debug(f'prepared tmp data for class {cls.__name__}: {data!r}')
        return data
    # end def

    @classmethod
    def process_callback_data(cls, data: CallbackData) -> None:
        """
        Processes the callback data.
        Raises an `AbortProcessingPlease` if it did find something valid to process.

        Here specifically, the callbacks with type `cls.MENU_TYPE` are handled.

        :param data: the callback data to handle
        :raises AbortProcessingPlease: If we have handled it.
        :return: None
        """
        logger.debug(f'{cls.__name__} got callback data: {data!r}')

        # check if we need to do pagination
        if data.type == cls.MENU_TYPE:
            assert isinstance(cls.menu_data, MenuData)
            button = data.value
            if not cast(MenuData, cls.menu_data).data:  # includes None
                logger.warn(f'{cls.__name__} has empty data for update!')
                cast(MenuData, cls.menu_data).data = cls.prepare_tmp_data()
            # end def
            logger.debug(f'Toggling checkbox {button!r} of menu {cls.__name__}, currently having the data {cast(MenuData, cls.menu_data).data}.')
            cast(MenuData, cls.menu_data).data[button] = not cast(MenuData, cls.menu_data).data[button]  # toggle the button.
            cls.refresh(done=False)
            raise AbortProcessingPlease()  # basically a subclass callstack safe "return None"
        # end if
        super().process_callback_data(data)
    # end def

    @classproperty
    def value(cls) -> Union[str, None]:
        from .buttons import CheckboxButton
        logger.debug(f'preparing display data for class {cls.__name__}.')
        button: CheckboxButton
        data = []
        if not cls.menu_data:
            return None
        # end if
        for button in cls.get_value(cls.checkboxes):
            if button.id in cls.menu_data and cls.menu_data[id]:
                data.append(button.title)
            # end if
        # end for
        return ", ".join(data)
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class RadioMenu(SelectableMenu):
    """
    Data storage is just the string of the selected value.
    """
    MENU_TYPE = 'radiobutton'  # used for CallbackData.type
    DATA_TYPE = str

    tmp_data_access: ClassVar[Union[None, DATA_TYPE]]
    saved_data_access: ClassVar[Union[None, DATA_TYPE]]

    radiobuttons: ClassValueOrCallable['RadioButton']

    @classmethod
    def get_buttons(cls) -> List[InlineKeyboardButton]:
        return cls._get_our_buttons(key='radiobuttons')
    # end def

    @classmethod
    def prepare_tmp_data(cls):
        """
        Prepares the data to initialize with on the first load.
        :return:
        """
        from telemenu.buttons import RadioButton
        logger.debug(f'preparing tmp data for class {cls.__name__}.')
        button: RadioButton
        data = None
        for button in cls.get_value(cls.radiobuttons):
            if button.default_selected:
                if data is not None:
                    raise ValueError('More than one RadioButton has a True default_selected attribute.')
                # end if
                data = button.value
            # end if
        # end for
        return data
    # end def

    @classmethod
    def process_callback_data(cls, data: CallbackData) -> None:
        """
        Processes the callback data.
        Raises an `AbortProcessingPlease` if it did find something valid to process.

        Here specifically, the callbacks with type `cls.MENU_TYPE` are handled.

        :param data: the callback data to handle
        :raises AbortProcessingPlease: If we have handled it.
        :return: None
        """
        logger.debug(f'{cls.__name__} got callback data: {data!r}')

        # check if we need to do pagination
        if data.type == cls.MENU_TYPE:
            assert isinstance(cls.menu_data, MenuData)
            button = data.value
            cls.menu_data.data = button
            cls.refresh(done=False)
            raise AbortProcessingPlease()  # basically a subclass callstack safe "return None"
        # end if
        super().process_callback_data(data)
    # end def

    @classproperty
    def value(cls) -> Union[str, None]:
        from .buttons import RadioButton
        logger.debug(f'preparing display data for class {cls.__name__}.')
        button: RadioButton
        data = []
        if not cls.menu_data:
            return None
        # end if
        for button in cls.get_value(cls.radiobuttons):
            if button.id == cls.menu_data:
                return button.title
            # end if
        # end for
        return None
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class SendMenu(Menu):
    """
    Superclass for all things which don't really have buttons, but instead needs something sent.
    """

    MENU_TYPE = 'send'
    TEXTUAL_BUTTON_TEXT_ALTERNATIVE = {  # True: has back button.
        True: "You can click /back to go back to the last menu or press /cancel to abort the whole process.",
        False: "You can press /cancel to abort the whole process."
    }

    @classmethod
    def get_buttons(cls) -> List[InlineKeyboardButton]:
        return []
    # end def

    @classmethod
    def get_keyboard(cls) -> Union[ReplyMarkup, None]:
        """
        We always return a force reply, as we don't do menu now, but just wanna have text/files/media/...
        :return:
        """
        return ForceReply(selective=True)
    # end def

    @classmethod
    def text(cls) -> str:
        """
        This is lacking translations, so you might have to overwrite it with your own texts...
        :return:
        """
        text = cls.get_value(super().text)
        return text
        return (
            text + "\n\n" +
            cls.TEXTUAL_BUTTON_TEXT_ALTERNATIVE[cls.get_back_button() is not None]
        )
    # end def

    @classmethod
    def get_back_button(cls) -> Union[None, 'telemenu.buttons.BackButton']:
        pass
    # end def

    @classmethod
    def reply_markup(cls) -> Union[None, ReplyMarkup]:
        return cls.get_keyboard()
    # end def

    @classmethod
    def prepare_tmp_data(cls):
        return None
    # end def

    @TeleMenuMachine.mark_for_register.on_command('cancel')
    @classmethod
    def _menu_on_cmd_cancel(cls, update: Update, text: Union[str, None]):
        from .buttons import HistoryButton, GotoButton
        button = cls.get_value(cls.cancel) if getattr(cls, 'cancel') else None
        logger.debug(f'Got a /cancel command, regiered button is {button!r}.')
        save = button.save if button and isinstance(button, HistoryButton) else False
        assert not button or not isinstance(button, HistoryButton) or (isinstance(button.save, bool) and not button.save)
        cls._menu_cmd_process(save=save, button=button)
    # end def

    @TeleMenuMachine.mark_for_register.on_command('back')
    @classmethod
    def _menu_on_cmd_back(cls, update: Update, text: Union[str, None]):
        from .buttons import HistoryButton, GotoButton
        button = cls.get_value(cls.cancel) if getattr(cls, 'back') else None
        logger.debug(f'Got a /back command, regiered button is {button!r}.')
        save = button.save if button and isinstance(button, HistoryButton) else None
        assert not button or not isinstance(button, HistoryButton) or (button.save is None)
        cls._menu_cmd_process(save=save, button=button)
    # end def

    @TeleMenuMachine.mark_for_register.on_command('done')
    @classmethod
    def _menu_on_cmd_done(cls, update: Update, text: Union[str, None]):
        from .buttons import HistoryButton, GotoButton
        button = cls.get_value(cls.done) if getattr(cls, 'done') else None
        logger.debug(f'Got a /done command, regiered button is {button!r}.')
        save = button.save if button and isinstance(button, HistoryButton) else True
        assert not button or not isinstance(button, HistoryButton) or (isinstance(button.save, bool) and button.save)
        cls._menu_cmd_process(save=save, button=button)
    # end def

    @classmethod
    def _menu_cmd_process(cls, save: Union[bool, None], button: Union['Button', Type['Menu']]):
        from .buttons import GotoButton, HistoryButton
        if isinstance(save, bool):
            if save:
                cls.save_data()
                cls.delete_tmp_data()
            else:
                cls.delete_tmp_data()
            # end if
        # end def
        assert not button or not isinstance(button, HistoryButton) or (isinstance(button.save, bool) and button.save)
        if button:
            if isinstance(button, GotoButton):
                button: GotoButton
                cls.switch_to_menu(button.menu)
            # end if
            if isinstance(button, HistoryButton):
                cls.switch_history(button.delta, save=save)
                raise AbortProcessingPlease(return_value='Okey, all done.')  # TODO l18n
            elif inspect.isclass(button) and issubclass(button, Menu):
                cls.switch_to_menu(button)
            # end if
        else:
            cls.switch_history(-1, save=save)
        # end if
        raise AbortProcessingPlease(return_value='Okey, all done.')  # TODO l18n
    # end if
# end class


@dataclass(init=False, eq=False, repr=True)
class TextMenu(SendMenu):
    """
    Simple reply text to this menu.
    Uses force reply.
    """
    MENU_TYPE = 'text'  # used for CallbackData.type

    @classmethod
    @abstractmethod
    def _parse(cls, text: str) -> JSONType:
        """
        Throw an ValueError or TypeError if you couldn't have that.
        Otherwise return the value to store.
        You can also return a `SendableMessageBase` to send that instead of storing the value, e.g. to reply a error message..

        :param text: The user input.
        :type  text: str

        :return: the value to store.
        :rtype: JSONType|SendableMessageBase
        """
        raise NotImplementedError('Subclasses must implement that.')
    # end def

    # noinspection PyUnusedLocal
    @TeleMenuMachine.mark_for_register.on_message('text')
    @classmethod
    def on_message_listener(cls, update: Update, msg: Message):
        from .buttons import GotoButton, HistoryButton, BackButton

        logger.debug(f'TextMenu ({cls.__name__}) got text update: {update!r} | {msg!r}')
        text = update.message.text.strip()

        if text.startswith('/'):
            logger.debug('Checking if command is command.')
            for command, listener in (('done', cls._menu_on_cmd_done), ('cancel', cls._menu_on_cmd_cancel), ('back', cls._menu_on_cmd_back)):
                # noinspection PyProtectedMember
                for prefix in cast(TeleStateMachineMenuSerialisationAdapter, cls.state_machine).teleflask._yield_commands(command):
                    logger.debug('Checking if command /{prefix}...')

                    if text == prefix:
                        raise AbortProcessingPlease(return_value=listener(update=update, text=None))
                    elif text.startswith(prefix + ' '):
                        cmd, text = tuple(text.split(" ", maxsplit=1))
                        raise AbortProcessingPlease(return_value=listener(update=update, text=None))
                    # end if
                # end for
            # end for
            logger.debug('No fitting command listener.')
        else:
            logger.debug('Not starting with a slash, so can\'t be a commend')
        # end if
        try:
            logger.debug(f'calling {cls.__name__}._parse({text!r}).')
            value = cls._parse(text)
            logger.debug(f'{cls.__name__}._parse({text!r}) returned {value!r}.')
        except (ValueError, TypeError):
            logger.debug(f'{cls.__name__}._parse({text!r}) could not be parsed.')
            return cls.get_value(cls.parsing_failure) if hasattr(cls, 'parsing_failure') else 'Could not parse.'
        # end try
        cls.menu_data.data = value
        cls.save_data()
        logger.debug(f'TextMenu ({cls.__name__}) stored data: {cls.menu_data.data!r}: {cls.menu_data!r}')
        success_message = cls.get_value(cls.parsing_success) if hasattr(cls, 'parsing_success') else None
        if success_message:
            return success_message
        # end if
        button = cls.get_value(cls.done) and hasattr(cls, 'done')
        if button:
            cls.save_data()
        # end def
        if not button:
            button = cls.get_value(cls.back) and hasattr(cls, 'back')
        # end if
        if not button:
            button = cls.get_value(cls.cancel) and hasattr(cls, 'cancel')
            if button:
                cls.delete_tmp_data()
            # end def
        # end if
        if not button:
            logger.warning('No button to go found, generating a back button')
            button = BackButton()
        if isinstance(button, GotoButton):
            button = button.menu
        # end if
        if inspect.isclass(button) and issubclass(button, Menu):
            cls.switch_to_menu(button)
        elif isinstance(button, HistoryButton):
            cls.switch_history(delta=button.delta, save=button.save)
        # end if
    # end def

    @classproperty
    def value(cls) -> Union[str, None]:
        logger.debug(f'preparing display data for class {cls.__name__}.')
        return repr(cls.menu_data.data)
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextStrMenu(TextMenu):
    """
    A force reply text string.
    """
    MENU_TYPE = 'text_str'  # used for CallbackData.type

    @classmethod
    def _parse(cls, text: str) -> JSONType:
        """
        Throw an ValueError or TypeError if you couldn't have that.
        Otherwise return the value to store.
        You can also return a `SendableMessageBase` to send that instead of storing the value, e.g. to reply a error message..

        :param text: The user input.
        :type  text: str

        :return: the value to store.
        :rtype: JSONType|SendableMessageBase
        """
        return text
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextIntMenu(TextMenu):
    """
    A force reply text string parsed as integer.
    """
    MENU_TYPE = 'text_int'  # used for CallbackData.type

    @classmethod
    def _parse(cls, text: str) -> JSONType:
        """
        Throw an ValueError or TypeError if you couldn't have that.
        Otherwise return the value to store.
        You can also return a `SendableMessageBase` to send that instead of storing the value, e.g. to reply a error message..

        :param text: The user input.
        :type  text: str

        :return: the value to store.
        :rtype: JSONType|SendableMessageBase
        """
        return int(text)
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextFloatMenu(TextMenu):
    """
    A force reply text string parsed as float.
    """
    MENU_TYPE = 'text_float'  # used for CallbackData.type

    def _parse(self, text: str) -> float:
        return float(text)
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextPasswordMenu(TextMenu):
    """
    A force reply text string which deletes your answer again.
    """
    MENU_TYPE = 'text_password'  # used for CallbackData.type
    def _parse(self, text: str) -> str:
        return text
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextEmailMenu(TextMenu):
    """
    A force reply text string which is validated as valid email.
    """
    MENU_TYPE = 'text_email'  # used for CallbackData.type

    def _parse(self, text: str) -> str:
        if "@" not in text or "." not in text:  # TODO: improve validation.
            raise ValueError('No good email.')
        return text
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextTelMenu(TextMenu):
    """
    A force reply text string which is validated as valid telephone number.
    """
    MENU_TYPE = 'text_tel'  # used for CallbackData.type

    def _parse(self, text: str) -> str:
        # TODO: add validation.
        return text
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextUrlMenu(TextMenu):
    """
    A force reply text string which is validated as valid url.
    """
    MENU_TYPE = 'text_url'  # used for CallbackData.type

    allowed_protocols: List[str] = dataclass_field(default_factory=lambda: ['http', 'https'])

    def _parse(self, text: str) -> str:
        if not any(text.startswith(protocol) for protocol in self.allowed_protocols):
            raise ValueError('Protocol not allowed')
        # end if
        # TODO: improve validation.
        return text
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class UploadMenu(SendMenu):
    """
    A force reply file upload.
    """
    MENU_TYPE = 'upload_file'  # used for CallbackData.type
    UPDATE_ATTRIBUTE = 'document'

    allowed_mime_types: Union[List[Union[str, Pattern]], None] = None
    allowed_extensions: Union[List[str], None] = None

    @TeleMenuMachine.mark_for_register.on_message
    @classmethod
    def on_message_listener(cls, update: Update, msg: Message):
        from pytgbot.api_types.receivable.media import PhotoSize
        if not hasattr(msg, cls.UPDATE_ATTRIBUTE):
            return None
        # end if
        file_attr = getattr(msg, cls.UPDATE_ATTRIBUTE)  # something like msg.document, msg.photo, ...
        if hasattr(file_attr, 'file_id'):  # Document, Video, Gif, Sticker, ...
            file_id = file_attr.file_id
        elif isinstance(file_attr, list):
            biggest_size = 0
            biggest_file = None
            for photo in file_attr:
                assert isinstance(photo, PhotoSize)
                if photo.file_size > biggest_size:
                    biggest_file = photo.file_id
                    biggest_size = photo.file_size
                # end if
            # end for
            file_id = biggest_file
        else:
            raise ValueError(f'Don\'t know how to handle `Message.{cls.UPDATE_ATTRIBUTE}`...')
        # end if

        return file_id
    # end def
# end class
