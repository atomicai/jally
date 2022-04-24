# -*- coding: utf-8 -*-
import json
from abc import ABC, ABCMeta
from typing import Type, List, Union, Dict, Callable, ClassVar, TypeVar, Generic, Any

from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType
from pytgbot import Bot
from pytgbot.api_types.receivable.updates import Update
from pytgbot.api_types.sendable.reply_markup import Button, KeyboardButton, InlineKeyboardButton, ForceReply, \
    ReplyKeyboardMarkup
from pytgbot.api_types.sendable.reply_markup import ReplyMarkup, InlineKeyboardMarkup
from teleflask.new_messages import TextMessage, SendableMessageBase
from teleflask.server.base import TeleflaskMixinBase
from teleflask.server.mixins import StartupMixin

from telestate import TeleState, TeleStateMachine
from .buttons import GotoMenuButton, ToggleButton, GotoStateButton

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class MenuMachine(object):
    def output_current_menu(self):
        pass
    # end def
# end class


T = TypeVar('T')  # Any type.
ClassValueOrCallable = ClassVar[Union[T, Callable[[Update], T]]]


class Menu(StartupMixin, TeleflaskMixinBase):
    """
    Menu for telegram (flask).
    Basically a TBlueprint, which will select the current state and process only those functions.

    It will load/save the state before/after processing the updates via the functions `load_state_for_chat_user` and `save_state_for_chat_user`.
    Those functions must be implemented via an extending subclass, so you can use different storage backends.

    Variables:
    - state.*
    - menu data
        - <placeholder for selected answer>
        - selected choice (especially as we remove the buttons if done)
        - multiple choices (if multiple checkboxes)
        - text (not as important, as your message is there)
    - metadata: (user_link, chat, time)
        - same as RulesRulesBot uses
    - history?

    There are the following steps:

    - Create new menu
        - Use cases:
            - Menu should be displayed (i.e. we are executing /open_menu)
        - Steps:
            - Generate      title, body, buttons  (`prepare_meta`)
            - Store         title, body, buttons, so actions can work later
            - Send Message  title, body, buttons  (`output_current_menu`)
            - Store Message ID (or full update?)
            - Update State to the Menu's state, listening for updates.
    - Edit existing menu
        - Use cases:
            - User toggles checkbox
            - User clicks pagination
        - Steps:
            - Listen for events
            - On event (e.g. inline button):
            - Load existing menu from state:  title, body, buttons
                - Find current menu
                - Create object from existing data (`self(**data)`)
            - Transform changes
                - Pagination
                - Checkbox
            - Store updated data
            - Edit Message  title, body, buttons  (`output_current_menu`)
    - Leave menu
        - Use cases:
            - /cancel
            - Navigation to a different menu
        - Steps
            - Listen for events
            - On event (e.g. inline button):
            - Load existing menu from state:  title, body, buttons
                - Find current menu
                - Create object from existing data (`self(**data)`)
            - Close Menu
                - Remove Buttons
                - Edit text to include chosen answer
                - or maybe: Delete completely
            - Update state to the one of the next Menus, or a specific state (/cancel: state DEFAULT).

    Approaches:
        - a) Mix and match button types
            - probably a bad idea because it's very complex.
            - also storage of multiple different types per page would be aweful.
            - not gonna do that.
        - b) Fixed Menu types
            - i.e. only one kind of buttons can be used per menu
                - maybe we can add sub-menu kind of thing at a later point.
                - Like left side vs right side?
                - if we ever gonna do that, it will be at a much later point in time.
            - Questions:
                - is this limited to a single user?
                    - can multiple user get access on a menu, say all admins in a group chat?
                    - we need a programmatic setting/method for that, how would that look like?
                - do we need some l18n?
                    - the library user can do that.
                - is state handled by the current menu or the actual state name?
                    - the current state name is derived from the menu name (or overwritten by ._id)
                    - also that state name is used to map the menu classes as well.
                    - this all happens with @telemenu.register
                - should we register showing a initial menu onto /start if freshly creating a TeleStateMachine?
                    - no, we don't know the main menu.
            - Features:
                - Wrap buttons into colums
                    - max 100 Buttons Total
                    - max 8 buttons per row.
                    - ✅ probably best to do like 5 rows 2 columns max.
                    - We need to allow custom formats.
                        - e.g. a cancel button would go over both columns, while having "Cancel", "Done" should be the same line.
                - Automatic pagination for all of those with too many buttons ≪/≫ (or maybe one of ⋘/⋙, ⏪/⏩, ◀️/▶️ or ⬅️/➡️)
                    - maybe first/last as well? ↖️/↘️, ⏮/⏭, 🔙/🔜, ⋘/⋙
                    - space for numbered pagination?
                        - e.g. [⋘|≪|2|3|4|≫|⋙] ＜＞ ⫷⫸ ⋖⋗ ≪≫ <>
                            - maybe 'show all' expand button for < 100 buttons?
                            - No emoji versions of numbers, they would go only up to 10: 2️⃣|3️⃣|4️⃣|...|9️⃣|🔟
                    - must be aware that the button list is dynamically generated
                        - if you are on page 10, and only 2 buttons are generated the next time, we need to jump back to page 1 (offset 0).
                - "Back to last menu" button: ⏏️, 🆙, 🛑, 🔙, ⃠, 🤚, 🚫 or simply Back
                    - Also registers /back
                    - ✅ edits menu in place (if possible)
                    - ✅ pops last entry from history-hierarchy.
                    - you can overwrite the menu to jump to, instead of returning to the last one.
                        - it should search the most recent version of that menu, and drop everything in between
                        - maybe `-5` would be possible?
                    - should this save changes?
                        - As "Done" and "Cancel" are doing a "Back" too, using a back button is simply invalid.
                            - We could check if we have unsaved data?
                            - Like track that in a `is_unsaved` property?
                            - And your button array which is generated by a function could switch out the "Done" with a "Back" if it's okey?
                - "Done" button:  🆗, ↩️, 🔚, ✔️, 🏁
                    - Also registers /done
                    - allows to jump to a different menu
                    - all but the GotoMenu? No. All. It is optional anyway.
                    - how should that be reflected in the "back" button history?
                        - a) you can indeed go back every menu
                        - b) you go back to the menu before all the `done` clicks.
                    - For example under a checkbox list, to store the changes.
                        - Shouldn't they be stored on every toggle anyway? In fact we need those for the toggle to work.
                        - How do we mark saved data?
                            - We need a separate data storage which is not the menu's current working data. See 'State Data' below.
                    - you can overwrite the menu to jump to, instead of returning to the last one.
                - "Cancel" button
                    - Alias to /cancel
                    - Basically "Done" but without saving the data.
                        - For example under a checkbox list
                    - you can specify a menu to jump to
                    - you can overwrite the menu/state to jump to, instead of setting the state to DEFAULT
                - Function buttons should stay at the bottom
                    - last two rows should be
                        - pagination (if applicable)
                        - everything jumping between menus, currently "Back", "Done" and "Cancel" buttons.
                - register /back, /done, /cancel
                    - command representation of the "Back", "Done" and "Cancel" buttons
                    - if not needed, i.e register with a fallback responding like "There's no going back now, sorry"
                - Automated data storage?
                    - checkboxes, text fields, dates, ... get variable names (to write to state.name) assigned
                        - a bit like argparse
                        - support multiple levels like state.dict.dict2.foo.bar
                    - what about files? base64?
                - the ID of buttons (button's callback data) gets assigned automatically
                    - based on the current state and the button action/value
                        - that means state name? function or blueprint name?
            - State data:
                - "menus": data of states, that's a dict, containing all the values
                    - '<ID_OF_MENU>': basically an archived version of "current" for each menu
                        - # "id": so we can identify the menu  -  this is the same as the key, so we won't need to actually store that as json, will be only be in the python version.
                        - "message_id": message id of last menu
                        - "page": page of pagination, default is 0.
                        - "data": this is a place for menu specific values and basically json.
                - "history" stack:
                    - list of visited menus
                    - e.g. ['MAIN_MENU', 'FIRST_MENU', 'SECOND_MENU']
                    - same id as in the "data" array.
                - "data" object:
                    - this is where the actual selections and stuff are stored to, whenever something is exited with "Done" (not. "Cancel").
            - Types:
                - Goto Menu
                    - switch to another menu
                        - append to history-hierarchy.
                    - basically edits the current message (if possible) to display a different menu
                    - ID: the current menu and the one switching to.
                    - Storage: Not needed.
                - Checkboxes (Toggle on/off) ❌/✅ — Aka. Multi-select
                    - Nullable Checkboxes (Toggle null/on/off) ❔/❌/✅ (Or maybe one of 🆓, 0️⃣, ➖ or ␀ ?)
                    - ID: the current menu and the index of the button.
                        - possibly user specified "<menu>_<user specified id>"
                    - Storage: Dict with booleans.
                - Radio Buttons (Only one can be on) 🔘/⚪️ — Aka. Dropdown
                    - checks the `selected` attribute to only be `True` on zero or one item.
                    - ID: based on the current menu and the index of the button.
                        - possibly user specified "<menu>_<user specified id>"
                        - better: have a value="1231" attribute, just like the HTML.
                    - Storage: the selected value or None.
                - Text input
                    - Force Reply
                        - This means no buttons :(
                            - maybe /cancel, /back and /done
                            - no /done
                                - makes no sense, as that would just be the submit, i.e. a sent message.
                                - hold on, what about edits?
                                    - we get those events, do we?
                                    - there is Update.edited_message
                                    - see below.
                            - just /cancel and /back then.
                                - which both abort
                                - should that be automatically included in the text messages?
                                - "You can click /back to go back to the last menu or /cancel to abort the current process."
                                - Here we actually need to think about l18n... :(
                            - Register the /cancel, and /back commands which should behave like normal buttons.
                    - Do we listen for edit events?
                        - maybe a /done after all?
                        - maybe that can re-trigger an action
                        - example: @Botfather
                            - Searching for free username
                            - "Oh no that one is already taken"
                                - can that be a validation?
                            - You have to send another text message, editing does nothing.
                            - Editing should work too.
                                - maybe include the text in the validation error?
                    - Predefined parsers (see html <input type="..."/>)
                        - text: unmodified
                        - number: int()
                        - float: float()
                        - password: attempt to delete the user's message and edit in a ••••• version into the answer.
                        - email: text with abc@uvw.xyz
                        - search: see 'text', maybe inline
                        - tel: something in some number format.
                        - url: valid looking URL, maybe optionally http(s) only?

                        - date: see 'Datepicker' below.
                        - month: see 'Datepicker' below.
                        - radio: see 'Radio Buttons' above.
                        - checkbox: see 'Checkboxes' above.
                        - time: see 'Datepicker' below
                        - week: see 'Datepicker' below
                    - ID: no id needed for text
                    - Storage: Just the value.
                - File Upload:
                    - html <input type="file" /> like.
                    - optional list of accepted mimetypes
                        - maybe tuples ('application', 'pdf'), ('text', None)
                        - or glob like  'application/pdf'  and  'text/*'
                        - regex maybe?  'application/pdf'  and  'text/[\\w-]+'
                    - optional list of accepted file suffixes
                        - no advanced regex or glob capabilities
                    - optional allow non-raw telegram types (photo, gif, video, ...)
                    - ID: no id needed for file upload
                    - Storage: Oh boy.
                        - Base64 encoded?
                        - Or some temp file like /tmp/upload-3zewnjbkkf.blob?
                - Datepicker: make a calender grid with the buttons, also allow text input.
                    - html <input type="..."/> like :
                        - date: year, month, day, no time(zone)
                            - format settable
                            - US, DE, ...
                            - own format string
                        - month:  month and year control, no time(zone)
                        - week:  week and year, no time(zone)
                        - time:  hours and minute, no timezone
                    - single components:
                        - year (buttons + num text)
                        - month (buttons + text (num or string))
                        - day (buttons + num text)
                        - weekday (buttons + text string)
                        - hour (buttons + num text)
                        - minute (buttons + num text)
                        - second (buttons + num text)
                        - timezone
                            - buttons and num text (+0200, -2, GTM)
                            - inline search button (GTM, Washington DC, Berlin, Paris, ...)
                    - combo components:
                        - automatically chains single components together to select a datetime thing.
                            - maybe via boolean flags?
                    - ID: based on the current menu
                        - in case of combo components also the type (yeah,hour,...)
                        - for timezone inline search the menu + the hour offset?
                    - Storage: ISO 8601 string.
                - Search: Use inline search?
                    - so basically it allows autocompletion, with an result Article, sending raw text.
                    - but could simply be a list of results to show, like the buttons.
                    - ID: selected element based on the current menu + query + index ?
                        - maybe that must be given by the user?
                            - so "<menu>_<user specified id>"
                    - Storage:
                        - text for ResultArticles?
                        - sticker id for Stickers?



    """
    state: TeleState
    # state: Union[TeleState, Callable[[TeleState], TeleState]]

    title: ClassValueOrCallable[str]
    title: str
    @classmethod
    def title(cls, update: Update) -> str:
        """
        Function returning the title to use.
        You can also set the title directly to a string, `title = 'foobar', instead of a `def title(self, update)` returning a string.

        The title is made bold, by wrapping the text into `<b>` and `</b>`.
        Note: You need to make sure the html is escaped where needed.

        The update is provided via parameter, also the function has access to the curret state (`self.state`).

        :param update: The telegram update which causes this menu to be rendered (e.g. a command, a click on the previous menu, etc.)
        :return:
        """
        raise NotImplementedError('Subclass must implement this.')
    # end def

    description: ClassValueOrCallable[str]  # html
    description: str  # html
    def description(cls, update: Update) -> str:
        """
        Function returning the description to use.
        You can also set the description directly to a string, `description = 'foobar', instead of a `def description(self, update)` returning a string.

        Note: You need to make sure the html is escaped where needed.

        The update is provided via parameter, also the function has access to the curret state (`self.state`).

        :param update: The telegram update which causes this menu to be rendered (e.g. a command, a click on the previous menu, etc.)
        :return:
        """
        raise NotImplementedError('Subclass must implement this.')
    # end def

    def __init__(self, telemachine: TeleStateMachine):
        super().__init__()
        if self.state is None:
            name = self.create_state_name(self.__class__.__name__)
            logger.debug(f'creating state for menu {self.__class__.__name__}: {name}')
            self.state = TeleState(name)
            telemachine.register_state(name, self.state)
        # end if
    # end def

    def prepare_meta(self, update: Update) -> Dict[str, JSONType]:
        """
        Prepares the data for usage in `output_current_menu`.

        :return: The dict with the prepared texts.
        """
        return {
            "title": self.title(update) if callable(self.title) else self.title,
            "description": self.description(update) if callable(self.description) else self.description,
        }
    # end def

    def output_current_menu(self, meta_data: Dict[str, JSONType]) -> SendableMessageBase:
        """
        Generates a message for this menu.

        :param meta_data:  Result of `self.prepare_meta(update=update)`.
        :return: Message to send
        """
        raise NotImplementedError('Subclasses should implement this')
    # end def

    # noinspection PyMethodMayBeStatic
    def format_text(self, title: str, description: str) -> str:
        """
        Formats a text containing tile and description in html.
        :param title:
        :param description:
        :return:
        """
        return (
            f"<b>{title}</b>\n"
            f"{description}"
        )
    # end def

    @staticmethod
    def create_state_name(cls_name):
        """
        Generates a name for the state to use, based on the class's name.

        :param cls_name:
        :return:
        """
        return f'__TELEMENU__{cls_name.upper()}'
    # end def

    def process_update(self, update):
        raise NotImplementedError('Subclasses should implement this')
    # end def

    def do_startup(self):
        super().do_startup()
    # end def
# end class


class AnswerMenu(Menu):
    def title(self, update: Update) -> str:
        return super().title(update)
    # end def

    def description(self, update: Update) -> str:
        return super().description(update)
    # end def

    def prepare_meta(self, state: TeleState) -> Dict[str, JSONType]:
        data = super().prepare_meta(state)
        return data
    # end def

    def output_current_menu(self, meta_data: Dict[str, JSONType]) -> SendableMessageBase:
        """
        Sends a text message where a user will answer to.

        :param meta_data:  Result of `self.prepare_meta(update=update)`.
        :return: Message to send.
        """
        return TextMessage(
            text=self.format_text(meta_data['title'], meta_data['description']),
            parse_mode="html",
            disable_web_page_preview=True,
            disable_notification=False,
            reply_markup=ForceReply(selective=True),
        )
    # end def

    def process_update(self, update):
        pass
    # end def

    def answer_parser(self, update: Update, text: str) -> Any:
        """
        Function being called to parse the text the user sent us in response.

        :param update: The answering update (text message, button press, etc.)
        :param text:   The extracted text.
        :return: A parsed value of the required format.
        """
        raise NotImplementedError('Subclass must implement this.')
    # end def
# end class


class ButtonMenu(Menu, ABC):
    type: Union[Type[Button], Type[KeyboardButton], Type[InlineKeyboardButton]]
    buttons: ClassValueOrCallable[List[Union[GotoMenuButton, GotoStateButton, ToggleButton]]]

    def prepare_meta(self, state: TeleState) -> Dict[str, JSONType]:
        data = super().prepare_meta(state)
        return {
            **data,
            "type": self.type.__name__,
            "buttons": self.buttons(state) if callable(self.buttons) else self.buttons,
        }
    # end def
# end class


class InlineButtonMenu(ButtonMenu, ABC):
    """
    Text message directly has some buttons attached.
    """
    type: Type = InlineKeyboardButton

    def output_current_menu(self, meta_data: Dict[str, JSONType]) -> SendableMessageBase:
        """
        Sends a text message with the menu.

        :param meta_data:  Result of `self.prepare_meta(update=update)`.
        :return: Message to send
        """
        return TextMessage(
            text=self.format_text(meta_data['title'], meta_data['description']),
            parse_mode="html",
            disable_web_page_preview=True,
            disable_notification=False,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=meta_data['buttons'],
            ),
        )
    # end def

    def process_update(self, update: Update):
        if not (update and update.callback_query and update.callback_query.data):
            # skip this menu
            return super().process_update(update)
        # end def
        assert update.callback_query.data
        data = json.loads(update.callback_query.data)

        # TODO

    # end def
# end class


class SendButtonMenu(ButtonMenu):
    """
    Send button menu is like a InlineButtonMenu, but replaces the user keyboard with buttons.
    This means the user could still enter his own value if he so desire.

    If a text doesn't match the provided buttons a custom `parse_text` function is called to get the result.
    """

    def output_current_menu(self, meta_data: Dict[str, JSONType]) -> SendableMessageBase:
        """
        Sends a text message with the menu.

        :param meta_data:  Result of `self.prepare_meta(update=update)`.
        :return: Message to send
        """
        return TextMessage(
            text=self.format_text(meta_data['title'], meta_data['description']),
            parse_mode="html",
            disable_web_page_preview=True,
            disable_notification=False,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=meta_data['buttons'],
                resize_keyboard=True,  # make smaller if not needed
                one_time_keyboard=True,  # remove after click
                selective=True,  # only the user
            ),
        )
    # end def

    def process_update(self, update):
        return super().process_update(update)
    # end def

    type = KeyboardButton
    buttons: List[GotoMenuButton]

    def answer_parser(self, update: Update, text: str) -> Any:
        """
        Function being called if no of the existing buttons matched.

        :param update: The answering update (text message, button press, etc.)
        :param text:   The extracted text.
        :return: A parsed value of the required format.
        """
        raise NotImplementedError('Subclass must implement this.')
    # end def
# end class

