import datetime

import aiogram.types
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, FSInputFile
from aiogram_dialog import StartMode, DialogManager
from aiogram_dialog.widgets.kbd import Button

from database.db import questions
from dialogs.states import StartSG


from docx import Document
from docx.shared import Inches
from docx2pdf import convert

from services.pdf_func import format_new_doc


async def go_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)


async def next_window(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()


async def make(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *args, **kwargs):
    data = dialog_manager.dialog_data

    doc = format_new_doc(data)
    # doc.add_page_break()
    doc.save(f'{callback.from_user.id}.docx')
    # convert(f'{callback.from_user.id}.docx', f'{callback.from_user.id}.pdf')
    # document = FSInputFile(filename=f'{callback.from_user.id}.pdf', path=f'{callback.from_user.id}.pdf')
    document = FSInputFile(filename=f'demo.docx', path=f'demo.docx')
    await callback.message.answer_document(document=document)
    await dialog_manager.start(StartSG.start)


