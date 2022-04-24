# -*- coding: utf-8 -*-
import re
from typing import Any, Union, cast

from luckydonaldUtils.exceptions import assert_type_or_raise
from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType
from pytgbot.api_types.receivable.updates import Update
from teleflask import TBlueprint, Teleflask
from teleflask.server.base import TeleflaskMixinBase
from teleflask.server.mixins import BotCommandsMixin, MessagesMixin, RegisterBlueprintsMixin, UpdatesMixin

__author__ = 'luckydonald'
__all__ = ["TeleStateUpdateHandler", "TeleState"]

from telestate.constants import KEEP_PREVIOUS

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


_STATE_NAMES_REGEX = '^[A-Z][A-Z0-9_]*$'  # case sensitive


def assert_can_be_name(name, allow_setting_defaults=False):
    """
    Raises an exception if the given string is an invalid state name.
    Uses :py:`TeleStateMachine.can_be_name` to decide.

    :param name: The name of the state we want.
    :type  name: str

    :param allow_setting_defaults: if CURRENT and DEFAULT should be allowed. Default: `False`, not allowed.
    :type  allow_setting_defaults: bool

    :return: If it is valid.
    :rtype:  bool

    :raises ValueError: Invalid name for a state
    """
    if not can_be_name(name, allow_defaults=allow_setting_defaults):
        raise ValueError(
            'Invalid Name. The state name must be capslock (fully upper case) can only contain numbers and '
            'the underscore.' + ('' if allow_setting_defaults else ' Also DEFAULT and CURRENT are not allowed.')
        )  # also start with an character
    # end if


# end def


def can_be_name(name: str, allow_defaults: bool = False) -> bool:
    """
    Check if a string is valid for usage as state name.

    :param name: The name of the state we want.
    :type  name: str

    :param allow_defaults: if CURRENT and DEFAULT should be allowed. Default: `False`, not allowed.
    :type  allow_defaults: bool

    :return: If it is valid.
    :rtype:  bool
    """
    if not name:
        return False
    # end if
    if not allow_defaults and name in ('CURRENT', 'DEFAULT', 'ALL'):
        return False
    # end if
    if not name.isupper():
        return False
    # end if
    return bool(re.match(_STATE_NAMES_REGEX, name))


# end def


class TeleStateUpdateHandler(RegisterBlueprintsMixin, BotCommandsMixin, MessagesMixin, UpdatesMixin, TeleflaskMixinBase):
    """
    This class does the actual @command, @on_update, etc. logic, by extending the mixins providing that functionality.

    TeleStateMachine.process_update will call the current state's TeleStateUpdateHandler's process_update, which will leave that to the mixins.
    """

    def __init__(self, wrapped_state, teleflask, *args, **kwargs):
        self.wrapped_state: TeleState = wrapped_state
        self.teleflask: Teleflask = teleflask
        super().__init__(*args, **kwargs)

    # end def

    def process_update(self, update):
        """
        This method is called from the flask webserver.

        Any Mixin implementing must call super().process_update(update).
        So catch exceptions in your mixin's code.

        :param update: The Telegram update
        :type  update: pytgbot.api_types.receivable.updates.Update
        :return:
        """
        logger.debug('State {!r} got an update.'.format(self))
        super().process_update(update)

    # end def

    @property
    def username(self):
        return self.wrapped_state.machine.username

    # end def

    @property
    def user_id(self):
        return self.wrapped_state.machine.user_id

    # end def

    def process_result(self, update, result):
        return self.wrapped_state.process_result(update, result)

    # end def

    def do_startup(self):
        super().do_startup()

    # end def


# end class


class TeleState(TBlueprint):
    """
    Basically the TeleState works like a TBlueprint, but is only active when that TeleState is active.
    """

    warn_on_modifications: bool = True

    machine: Union['TeleStateMachine', None]
    data: Union[Any, None]
    update: Union[Update, None]  # store the update activation this. Used for sending/updating menus.
    update_handler: Union[TeleStateUpdateHandler, None]

    def __init__(self, name=None, machine: 'TeleStateMachine' = None):
        """
        A new state.

        :param name: Name of the state
        :param data: additional data to keep for that state
        :param machine: Statemachine to register with
        """
        if name:
            assert_can_be_name(name, allow_setting_defaults=True)
        # end if
        from .machine import TeleStateMachine

        assert_type_or_raise(machine, TeleStateMachine, None, parameter_name='machine')
        assert machine is None or isinstance(machine, TeleStateMachine)

        self.machine: Union[TeleStateMachine, None] = None  # set by self.register_machine(...), below
        self.data = None
        self.update = None
        self.update_handler: Union[TeleStateUpdateHandler, None] = None
        super(TeleState, self).__init__(name)  # writes self.name

        if machine:
            self.register_machine(machine)
        # end def

    # end def

    def register_teleflask(self, teleflask):
        logger.debug(f'Registering update_handler for {self.name!r}: {teleflask!r}')
        if self._got_registered_once:
            logger.warning('already registered')
            return
        # end if
        self.update_handler = TeleStateUpdateHandler(self, teleflask)
        self.update_handler.register_tblueprint(self)

    # end def

    def activate(self, data: Any = None, update: Union[Update, None, KEEP_PREVIOUS.__class__] = KEEP_PREVIOUS):
        """
        Sets this state as new current step.

        :param data: additional data to store in that state.
        :param update: The Telegram Update this state is based on. Default is KEEP_PREVIOUS,
                       so if you activate this state without specifying an different value for this,
                       the update will stay the same for the new chosen state.
        """
        from telestate import TeleStateMachine

        assert_type_or_raise(update, Update, None, KEEP_PREVIOUS.__class__, parameter_name='update')
        cast(TeleStateMachine, self.machine).set(self, data=data, update=update)

    # end def

    def register_machine(self, machine, name=None):
        """
        Registers an bot to use with the internal blueprint.

        :param machine: Instance of the statemachine to register to.
        :type  machine: TeleStateMachine:
        :param name: Optionally you can overwrite the name.
        :type  name: str
        """
        logger.debug('registering with machine {!r} at name {!r}.'.format(machine, name))
        self.machine = machine
        if name:
            self.name = name
        # end if

    # end def

    def record(self, func):
        if self.update_handler is None:
            return super().record(func)
        # end def

        # in case we already have update_handler
        logger.warning(f'late addition to {self.name}: {func}')
        state = self.make_setup_state(self.update_handler, {}, first_registration=False)
        func(state)
        # end for

    # end def

    def process_result(self, update, result):
        """
        Send the result.
        It may be a :class:`Message` or a list of :class:`Message`s
        Strings will be send as :class:`TextMessage`, encoded as raw text.

        :param update: A telegram incoming update
        :type  update: TGUpdate

        :param result: Something to send.
        :type  result: Union[List[Union[Message, str]], Message, str]

        :return: List of telegram responses.
        :rtype: list
        """
        self.machine.process_result(update, result)

    # end def

    def __repr__(self):
        return "<{clazz} {name!r}>".format(clazz=self.__class__.__name__, name=self.name)

    # end def

    __str__ = __repr__

    @property
    def teleflask(self):
        return self.machine.teleflask

    # end def

    @property
    def bot(self):
        """
        Returns the pytgbot Bot instance.
        :return:
        :rtype: pytgbot.bot.Bot
        """
        return self.machine.bot

    # end def

    @property
    def username(self):
        return self.machine.username

    # end def

    @property
    def user_id(self):
        return self.machine.user_id

    # end def

    def set_data(self, data: Union[JSONType, Any]):
        self.data = data

    # end def

    def set_update(self, update: Union[Update, None]):
        self.update = update

    # end def


# end class
