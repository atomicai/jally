#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import abstractmethod
from typing import Tuple, Union
from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class TeleStateDatabaseDriver(object):
    @abstractmethod
    def load_state_for_chat_user(
        self,
        chat_id: Union[int, str, None],
        user_id: Union[int, str, None]
    ) -> Tuple[Union[str, None], JSONType]:
        """
        Loads a state, and sets it.

        :param chat_id: ID of the user/group chat.
        :param user_id: ID of the user.

        :return: Tuple of the name of the state and optionally data.
        """
        raise NotImplementedError('Your database driver subclass must implement this.')
    # end def

    @abstractmethod
    def save_state_for_chat_user(
        self,
        chat_id: Union[int, str, None],
        user_id: Union[int, str, None],
        state_name: str,
        state_data: JSONType
    ) -> None:
        """
        Saves the current state.

        :param chat_id: ID of the user/group chat.
        :param user_id: ID of the user.
        :param state_name: the name of the current state.
        :param state_data: the additional data for that state.

        :return: Nothing.
        """
        raise NotImplementedError('Your database driver subclass must implement this.')
    # end def
# end class
