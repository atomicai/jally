# -*- coding: utf-8 -*-
from typing import Tuple, Union, Optional

from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType
from pymongo.collection import Collection

from ..database_driver import TeleStateDatabaseDriver

__author__ = 'luckydonald'
__all__ = ['MongoDriver']
logger = logging.getLogger(__name__)


class MongoDriver(TeleStateDatabaseDriver):
    """
    A TeleStateMachine implementation preserving it's values in a mongo db instance.

    It will store im the format of
    ```py
    {
        'chat_id': chat_id,
        'user_id': user_id,
        'state': state_name,
        'data': state_data,
    }
    ```
    Note, if `user_id` or `chat_id` are `None`, that will be stored as `"null"`. See `msg_get_chat_and_user_mongo_prepared(...)`
    """
    def __init__(self, mongodb_table):
        assert isinstance(mongodb_table, Collection)
        self.mongodb_table = mongodb_table
        super().__init__()
    # end def

    def load_state_for_chat_user(
        self,
        chat_id: Union[int, str, None],
        user_id: Union[int, str, None]
    ) -> Tuple[Optional[str], JSONType]:
        chat_id, user_id = self.msg_get_chat_and_user_mongo_prepared(chat_id, user_id)
        data = self.mongodb_table.find_one(
            filter={'chat_id': chat_id, 'user_id': user_id},
        )
        if not data:
            return None, None
        # end if
        return data['state'], data['data']
    # end def

    @staticmethod
    def msg_get_chat_and_user_mongo_prepared(
        chat_id: Union[int, str, None],
        user_id: Union[int, str, None]
    ) -> Tuple[Union[int, str], Union[int, str]]:
        """
        Like `update_get_chat_and_user(update)`,
        extracts the chat_id and user_id from an update,
        but replaces `None` with the string `"null"`.

        :param chat_id: ID of the user/group chat.
        :param user_id: ID of the user.

        :return: tuple of (chat_id, user_id)
        """
        chat_id = 'null' if chat_id is None else chat_id
        user_id = 'null' if user_id is None else user_id
        return chat_id, user_id
    # end def

    def save_state_for_chat_user(
        self,
        chat_id: Union[int, str, None],
        user_id: Union[int, str, None],
        state_name: str,
        state_data: JSONType
    ) -> None:
        chat_id, user_id = self.msg_get_chat_and_user_mongo_prepared(chat_id, user_id)
        self.mongodb_table.replace_one(
            filter={'chat_id': chat_id, 'user_id': user_id},
            replacement={
                'chat_id': chat_id,
                'user_id': user_id,
                'state': state_name,
                'data': state_data,
            }
        )
    # end def
# end class
