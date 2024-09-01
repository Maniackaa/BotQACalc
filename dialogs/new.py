import asyncio
import copy
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
from database.db import questions, get_count, steps_group, get_price, get_yazik_count, get_yazik_price, \
    get_peremichka_count
from dialogs.buttons import make
from dialogs.custom_class import GroupCustom

from dialogs.states import StartSG, AddCarSG, NewDialog


async def getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    count = data.get('count', 1)
    data['count'] = count
    data['step1'] = data.get('step1', [])
    data['step2'] = data.get('step2', [])
    data['step3'] = data.get('step3', [])

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
    if count == 6:  # Введите количество комплектов
        answers = [str(get_count(data.get('3')))]  # Какие коврики нужны?
    if count == 7:  # Введите стоимость комплекта
        answers = [str(get_price(data.get('4')))]  # Выберите комплектацию ковриков или введите свой вариант?
    if count == 11:  # Введите кол-во язычков
        answers = [str(get_yazik_count(data.get('10')))]  # Выберите тип язычка
    if count == 12:  # Введите стоимость язычка
        answers = [str(get_yazik_price(data.get('10')))]  # Выберите тип язычка
    if count == 15:  # Введите кол-во перемычек
        answers = [str(get_peremichka_count(data.get('14')))]  # Выберите тип перемычки
    result = {'count': count, 'question': question, 'answers': answers, 'width': width, 'q_content_type': q_content_type, 'back': count > 1}
    return result


async def result_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    text = ''
    for q_num in questions:
        print(q_num, questions[q_num].get('q'))
        text += f'{q_num}. {questions[q_num].get("q")}\n{data.get(str(q_num))}\n\n'
    return {'text': text}


async def next_q(dialog_manager, change_count=0):
    data = dialog_manager.dialog_data
    count = data.get('count', 0)
    logger.debug(f'next_q: count: {count}, {change_count}')
    if change_count:
        count = change_count

    if count == 25:  # Выберите тип прострочки окантовки?
        count += 2

    if count == 24:  # Выберите тип прострочки окантовки?
        if data.get('24') == 'Двойная':
            logger.debug('if count == 24 "Двойная"')
            count += 1

    if count == 28 and data.get('28') != 'Да':  # Есть ли микрокант?
        count += 1

    if count == 33 and data.get('33') != 'Да':  # Нужны ли вышивки??
        count += 3

    if count == 37 and data.get('37') != 'Да':  # Нужны ли дополнительные опции?
        count += 5

    if count == 43:  # Прикрепить фото?
        logger.debug('if count == 43')
        if data.get('43') == 'Нет':
            logger.debug(f"data.get('43'): {data.get('43')}")
            count += 3
    count += 1
    logger.debug(f'result count: {count}')
    data.update(count=count)
    logger.debug(f'result_data: {data}')
    if count not in questions:
        logger.debug('Вопросы закончились')
        logger.debug(data)
        await dialog_manager.next()


async def prev_q(callback: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    count = data.get('count', 0)
    count -= 1
    data.update(count=count)


async def item_select(callback: CallbackQuery, widget: Select,
                      dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    count = data.get('count', 0)
    selected = item_id
    logger.debug(f'selected {count}: {selected}')
    await callback.message.answer(selected)
    await callback.message.delete()
    data[str(count)] = selected
    logger.debug(data)
    if count == steps_group[1]['end'] and selected in ['Да', 'Нет']:  # 'Добавить еще комлпект'
        comment = data['8']
        comment = '' if comment == 'Нет' else comment
        current_step1 = [data['3'], data['4'], data['5'], data['6'], data['7'], comment]
        logger.debug(f'current_step1: {current_step1}')
        old_step1 = data['step1']
        old_step1.append(current_step1)
        data['step1'] = old_step1
        if selected == 'Да':
            # data['count'] = steps_group[1]['end'] - 1
            await next_q(dialog_manager, steps_group[1]['start'] - 2)
    if count == steps_group[2]['end'] and selected in ['Да', 'Нет']:  # Нужны ли еще дополнительные опции?
        logger.debug(f'Нужны ли еще дополнительные опции? {selected}')
        current_step2 = [data['38'], data['39'], data['40'], data['41']]
        old_step2 = data['step2']
        old_step2.append(current_step2)
        data['step2'] = old_step2
        if selected == 'Да':
            logger.debug("selected == 'Да'")
            logger.debug(f'selected == "Да". Change count = "{steps_group[2]["start"] - 2}"')
            await next_q(dialog_manager, steps_group[2]['start'] - 2)

    if count == steps_group[3]['end'] and selected in ['Да', 'Нет']:  # Прикрепить еще фото
        logger.debug(f'Прикрепить еще фото? {selected}')
        current_step3 = [data['44'], data['45']]
        old_step3 = data['step3']
        old_step3.append(current_step3)
        data['step3'] = old_step3
        if selected == 'Да':
            logger.debug("selected == 'Да'")
            logger.debug(f'selected == "Да". Change count = "{steps_group[3]["start"] - 2}"')
            await next_q(dialog_manager, steps_group[3]['start'] - 2)

    await next_q(dialog_manager)


async def check_type(message, dialog_manager):
    print(message.content_type, dialog_manager.dialog_data)
    q_content_type = dialog_manager.dialog_data['q_content_type']
    count = dialog_manager.dialog_data['count']
    if not questions[count].get('variable_answer') and q_content_type == ContentType.TEXT:
        return False
    check_func = questions[count].get('check_func')
    if check_func:
        try:
            result = check_func(message.text)
            logger.debug(f'result check_func: {result}')
        except Exception as e:
            logger.warning(e)
            return False
    return q_content_type == message.content_type


async def message_handler(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager) -> None:
    logger.debug(f'Отправлен тип {message.content_type}')
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

