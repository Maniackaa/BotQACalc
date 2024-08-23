import pickle
from pprint import pprint

from aiogram import Router, Bot
from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.types import User, CallbackQuery, Message, Update
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode
from aiogram_dialog.widgets.input import MessageInput, TextInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select, Url, Column, Back, Next, Start
from aiogram_dialog.widgets.text import Format, Const

from config.bot_settings import settings, logger

from dialogs.states import StartSG, AddCarSG, ProfileSG, NewDialog

router = Router()


async def start_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug('start_getter', dialog_data=data, start_data=dialog_manager.start_data)

    hello_text = f'Выберите действие'
    items = (
        # (-1002092051636, 'Тестовый канал'),
        ('new', '✅Новый опрос'),
    )
    return {'username': event_from_user.username, 'hello_text': hello_text, 'items': items}


async def channel_select(callback: CallbackQuery, widget: Select,
                         dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    data.update(channel_id=item_id)
    await dialog_manager.start(NewDialog.question, data=data)
    # await dialog_manager.start(AddCarSG.photo, data=data)


start_dialog = Dialog(
    Window(
        Format(text='{hello_text}'),
        Column(
            Select(Format('{item[1]}'),
                   id='start_poll',
                   on_click=channel_select,
                   items='items',
                   item_id_getter=lambda x: x[0]),
        ),
        state=StartSG.start,
        getter=start_getter,
    ),

)




