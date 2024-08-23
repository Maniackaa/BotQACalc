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


async def go_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)


async def next_window(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()


async def make(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *args, **kwargs):
    data = dialog_manager.dialog_data

    document = Document()

    document.add_heading(f'{callback.from_user.full_name}  {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}', 0)

    for q_num in questions:
        q = questions[q_num].get('q')
        q_content_type = questions[q_num].get('q_content_type', ContentType.TEXT)
        anwer = data[str(q_num)]
        print(q_content_type, q)
        print(anwer)
        document.add_heading(q, level=1)
        if q_content_type == ContentType.TEXT:
            document.add_paragraph(anwer, style='Intense Quote')
        elif q_content_type == ContentType.PHOTO:
            file_path = f'{callback.from_user.id}_photo_{q_num}.jpg'
            print(file_path)
            document.add_picture(file_path, width=Inches(3), height=Inches(3))

    # document.add_page_break()
    document.save(f'{callback.from_user.id}.docx')
    convert(f'{callback.from_user.id}.docx', f'{callback.from_user.id}.pdf')
    doc = FSInputFile(filename=f'{callback.from_user.id}.pdf', path=f'{callback.from_user.id}.pdf')
    await callback.message.answer_document(document=doc)
    await dialog_manager.start(StartSG.start)


