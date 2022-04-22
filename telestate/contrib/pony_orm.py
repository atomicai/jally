# -*- coding: utf-8 -*-
from typing import Type, Union, Tuple, Optional

from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType
from pony import orm

from ..database_driver import TeleStateDatabaseDriver


__author__ = 'luckydonald'
__all__ = ['PonyDriver']

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class PonyDriver(TeleStateDatabaseDriver):
    """
     A TeleStateMachine implementation preserving it's values in a sql instance via PonyORM.
    """

    class State(object):
        """
        Just a fake class proving typing annotations to the StateTable class
        """
        user_id: int
        chat_id: int
        state: str
        data: dict

        def __init__(self):
            raise NotImplementedError(
                "This is only for providing typing annotations to the IDEs, and shouldn't be used anywhere!")
        # end def
    # end class
    StateTable: Type[State]

    def __init__(self, db: orm.Database, state_table=None, state_upsert_lock=None):
        """
        A TeleStateMachine implementation preserving it's values in a sql instance via PonyORM.
        :param db: The database instance to append our tables to.
        :param state_table: overwrite the db.State table. If None, the generate one will be accessible at `self.StateTable`.
        :param state_upsert_lock: overwrite the db.StateUpsertLock table. If None, the generate one will be accessible at `self.UpsertLockTable`.
        """
        super().__init__()

        if state_table is not None:
            assert issubclass(state_table, self.State), "Needs to be subclass of PonyDriver.State"
            self.StateTable = state_table
        else:
            class State(db.Entity, self.State):
                id = orm.PrimaryKey(int, auto=True)
                user_id = orm.Optional(int, size=32, default=None, index=True, nullable=True)  # can be None (e.g. channels)
                chat_id = orm.Optional(int, size=64, default=None, index=True, nullable=True)  # can be None (e.g. inline_query)
                state = orm.Required(str)
                data = orm.Optional(orm.Json, default=None, nullable=True)  # can be None
            # end class
            self.StateTable = State
        # end if
        if state_upsert_lock is not None:
            self.UpsertLockTable = state_upsert_lock
        else:
            class StateUpsertLock(db.Entity):
                pass
            # end class
            self.UpsertLockTable = StateUpsertLock
        # end if
    # end def

    @orm.db_session
    def load_state_for_chat_user(
        self,
        chat_id: Union[int, str, None],
        user_id: Union[int, str, None]
    ) -> Tuple[Optional[str], JSONType]:
        db_state = self.StateTable.get(chat_id=chat_id, user_id=user_id)
        if not db_state:
            # switch into the default state
            return None, None
        # end if
        return db_state.state, db_state.data
    # end def

    @orm.db_session
    def save_state_for_chat_user(
        self,
        chat_id: Union[int, str, None],
        user_id: Union[int, str, None],
        state_name: str,
        state_data: JSONType
    ) -> None:

        ul = self.UpsertLockTable.select().for_update().first()  # enforce only one is in a session.
        logger.debug(f"Searching entry for chat {chat_id} and user {user_id}.")
        # noinspection PyUnresolvedReferences
        db_state = self.StateTable.get(
            chat_id=chat_id,
            user_id=user_id
        )
        if db_state:
            logger.debug(f"Found existing entry for chat {chat_id} and user {user_id}. Last state: {db_state.state!r}")
            db_state.set(
                chat_id=chat_id,
                user_id=user_id,
                state=state_name,
                data=state_data,
            )
        else:
            logger.debug(f"Creating new entry for chat {chat_id} and user {user_id} with state {state_name!r} and data:\n{state_data!r}.")
            # noinspection PyArgumentList
            self.StateTable(
                chat_id=chat_id,
                user_id=user_id,
                state=state_name,
                data=state_data,
            )
        # end if
    # end def
# end class
