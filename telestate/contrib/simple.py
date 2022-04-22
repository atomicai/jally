# -*- coding: utf-8 -*-
from typing import Union, Tuple, Optional

from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType

from ..database_driver import TeleStateDatabaseDriver

__author__ = 'luckydonald'
__all__ = ['SimpleDictDriver']
logger = logging.getLogger(__name__)


class SimpleDictDriver(TeleStateDatabaseDriver):
    """
    A TeleStateMachine implementation preserving it's values in an in-memory python dict.

    Stored like `cache[chat_id][user_id] = (state, data)`:
    ```py
    {
        '1000123123112': {
            '1234': (
                'DEFAULT',
                {'some': 1, 'random': None, 'data': ['yay', 'wooho', 111]}
            )
        },
    }
    """
    def __init__(self):
        logger.debug('creating new SimpleDictDriver instance.')
        self.cache = dict()  # {'chat_id': {'user_id': 'state'}}
        super().__init__()
    # end def

    def load_state_for_chat_user(
        self,
        chat_id: Union[int, str, None],
        user_id: Union[int, str, None]
    ) -> Tuple[Optional[str], JSONType]:
        logger.debug('states: {!r}'.format(self.cache))
        cache_data = self.cache.get(chat_id, {})
        # cache_data now contains all the users for the current chat, as dict.
        state_name, cache_data = cache_data.get(user_id, (None, None))
        # cache_data now is the state's data or None,
        # state_name is the state's name or None.
        logger.debug(f'cached state for {chat_id}|{user_id}: {state_name!r}\ndata: {cache_data!r}')
        if state_name:
            return state_name, cache_data
        else:
            logger.debug('no state found for update.')
            return None, None
        # end def
    # end def

    def save_state_for_chat_user(
        self,
        chat_id: Union[int, str, None],
        user_id: Union[int, str, None],
        state_name: str,
        state_data: JSONType
    ) -> None:
        logger.debug(f'storing state for {chat_id}|{user_id}: {state_name!r}\ndata: {state_data!r}')

        if chat_id not in self.cache:
            # chat_id level does not exist, create, with the {user_id: (state_name, data)} already inserted.
            self.cache[chat_id] = {user_id: (state_name, state_data)}
        else:
            # chat_id level does exist, just store the state in the user_id dict element. This can overwrite.
            self.cache[chat_id][user_id] = (state_name, state_data)
        # end if
        logger.debug('states: {!r}'.format(self.cache))
    # end def
# end class
