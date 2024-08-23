from itertools import chain
from typing import Dict, Iterable, List, Optional

from aiogram.types import CallbackQuery, InlineKeyboardButton

from aiogram_dialog.api.internal import ButtonVariant, RawKeyboard
from aiogram_dialog.api.protocols import DialogManager, DialogProtocol
from aiogram_dialog.widgets.common import WhenCondition
from aiogram_dialog.widgets.kbd import Group, Keyboard


class GroupCustom(Keyboard):
    def __init__(
            self,
            *buttons: Keyboard,
            id: Optional[str] = None,
            width: int = None,
            when: WhenCondition = None,
    ):
        super().__init__(id=id, when=when)
        self.buttons = buttons
        self.width = width

    def find(self, widget_id):
        widget = super(Group, self).find(widget_id)
        if widget:
            return widget
        for btn in self.buttons:
            widget = btn.find(widget_id)
            if widget:
                return widget
        return None

    async def _render_keyboard(
            self,
            data: Dict,
            manager: DialogManager,
    ) -> RawKeyboard:
        self.width = data.get('width', 1)
        kbd: RawKeyboard = []
        for b in self.buttons:
            b_kbd = await b.render_keyboard(data, manager)
            if not kbd:
                kbd.append([])
            kbd[0].extend(chain.from_iterable(b_kbd))
        if data.get('width', 1) and kbd:
            kbd = self._wrap_kbd(kbd[0])
        return kbd

    def _wrap_kbd(
            self,
            kbd: Iterable[InlineKeyboardButton],
    ) -> RawKeyboard:
        res: RawKeyboard = []
        row: List[ButtonVariant] = []
        for b in kbd:
            row.append(b)
            if len(row) >= self.width:
                res.append(row)
                row = []
        if row:
            res.append(row)
        return res

    async def _process_other_callback(
            self,
            callback: CallbackQuery,
            dialog: DialogProtocol,
            manager: DialogManager,
    ) -> bool:
        for b in self.buttons:
            if await b.process_callback(callback, dialog, manager):
                return True
        return False