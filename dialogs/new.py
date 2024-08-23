import asyncio
import datetime
import pickle
from itertools import chain
from pprint import pprint
from typing import Optional, Dict, Iterable, List

from aiogram import Router, Bot, F
from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.types import User, CallbackQuery, Message, Update, InputMediaPhoto, InlineKeyboardButton
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode, DialogProtocol
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.api.internal import RawKeyboard, ButtonVariant
from aiogram_dialog.widgets.common import ManagedScroll, WhenCondition
from aiogram_dialog.widgets.input import MessageInput, TextInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select, Url, Column, Back, Next, StubScroll, Group, NumberedPager, \
    SwitchTo, Start, Keyboard
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format, Const

from config.bot_settings import settings, logger
from database.db import questions
from dialogs.buttons import make
from dialogs.custom_class import GroupCustom

from dialogs.states import StartSG, AddCarSG, NewDialog


async def getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    count = data.get('count', 1)
    data['count'] = count

    question = questions[count]['q']
    answers = questions[count].get('a', [])
    if answers:
        max_width = len(max(answers, key=len))
        width = 50 // max_width
        logger.debug(f'width: {width}')
    else:
        width = 0
    q_content_type = questions[count].get('q_content_type', ContentType.TEXT)
    data.update(q_content_type=q_content_type)
    result = {'count': count, 'question': question, 'answers': answers, 'width': width, 'q_content_type': q_content_type, 'back': count > 1}
    return result


async def result_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    text = ''
    for q_num in questions:
        text += f'{q_num}. {questions[q_num].get("q")}\n{data.get(str(q_num))}\n\n'
    return {'text': text}


async def next_q(dialog_manager):
    data = dialog_manager.dialog_data
    count = data.get('count', 0)
    count += 1
    data.update(count=count)
    if count not in questions:
        logger.debug('Вопросы закончились')
        logger.debug(data)
        await dialog_manager.next()


async def prev_q(callback: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    count = data.get('count', 0)
    count -= 1
    data.update(count=count)


async def text_input(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    count = data.get('count', 0)
    field = str(count)
    data[field] = text
    await next_q(dialog_manager)


async def item_select(callback: CallbackQuery, widget: Select,
                      dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    count = data.get('count', 0)
    selected = item_id
    logger.debug(f'selected: {selected}')
    data[str(count)] = selected
    await next_q(dialog_manager)


async def check_type(message, dialog_manager):
    print(message.content_type, dialog_manager.dialog_data)
    q_content_type = dialog_manager.dialog_data['q_content_type']
    return q_content_type == message.content_type


async def message_handler(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager) -> None:
    logger.debug(f'Отправлено {message.content_type}')
    data = dialog_manager.dialog_data
    count = data.get('count', 0)
    field = str(count)
    check = await check_type(message, dialog_manager)
    if not check:
        return
    if message.content_type == ContentType.TEXT:
        logger.debug('Текст')
        data[field] = message.text
    elif message.content_type == ContentType.PHOTO:
        logger.debug('Фото')
        data[field] = message.photo[-1].file_id
        file_path = f'{message.from_user.id}_photo_{count}.jpg'
        await message.bot.download(file=message.photo[-1], destination=file_path)

    await next_q(dialog_manager)
    return

new_dialog = Dialog(
    Window(
        Format(text='{question}'),
        GroupCustom(
            Select(Format('{item}'),
                   id='answer_select',
                   on_click=item_select,
                   items='answers',
                   item_id_getter=lambda x: x),
            width=2,
            when='answers',
        ),
        MessageInput(
            func=message_handler,
            content_types=ContentType.ANY,
        ),
        Button(text=Const('Назад'),
               id='prev_q',
               on_click=prev_q,
               when='back'
               ),
        state=NewDialog.question,
        getter=getter,
    ),
    Window(
        Format(text='{text}'),
        Button(text=Const('Сделать док'),
               id='make',
               on_click=make,
               ),
        state=NewDialog.result,
        getter=result_getter,
    )
)

