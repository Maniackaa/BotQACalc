import asyncio
import pickle
from pprint import pprint

from aiogram import Router, Bot, F
from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.types import User, CallbackQuery, Message, Update, InputMediaPhoto
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import MessageInput, TextInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select, Url, Column, Back, Next, StubScroll, Group, NumberedPager, \
    SwitchTo, Start, Cancel
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format, Const

from config.bot_settings import settings, logger
from dialogs.add_car import text_input
from dialogs.buttons import go_start
from dialogs.states import StartSG, AddCarSG, ProfileSG, BalanceSG
from dialogs.type_factorys import positive_int_check, tel_check
from services.db_func import get_or_create_user


async def profile_getter(dialog_manager: DialogManager,
                         event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug(f'{data}')
    user = get_or_create_user(event_from_user)
    hello_text = f'Ваш баланс {user.balance} руб.'
    return {'hello_text': hello_text}


async def balance_button(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *args, **kwargs):
    data = dialog_manager.dialog_data


profile_dialog = Dialog(
    Window(
        Format(text='{hello_text}'),
        Start(
            Format("Пополнить баланс"),
            id="balance",
            state=BalanceSG.start
        ),
        Cancel(Const('Назад')),
        state=ProfileSG.start,
        getter=profile_getter,
    ),
)


async def balance_getter(dialog_manager: DialogManager,
                         event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug(f'{data}')
    user = get_or_create_user(event_from_user)
    file_id = data.get('photo', '')
    image = MediaAttachment(ContentType.PHOTO, file_id=MediaId(file_id))
    return {'photo': image, 'file_id': file_id}


async def pay_photo(message: Message, widget: MessageInput, dialog_manager: DialogManager) -> None:
    data = dialog_manager.dialog_data
    data['photo'] = message.photo[-1].file_id


async def send_pay_check(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *args, **kwargs):
    data = dialog_manager.dialog_data

balance_dialog = Dialog(
    Window(
        Format(text='Укажите сумму в рублях'),
        TextInput(
            id='amount',
            type_factory=positive_int_check,
            on_success=text_input,
        ),
        Cancel(Const('Назад')),
        state=BalanceSG.start,
    ),
    Window(
        Const(text='Приложите скриншот чека об оплате и нажмите ОК'),
        DynamicMedia('photo', when='file_id'),
        MessageInput(
            func=pay_photo,
            content_types=ContentType.PHOTO,
        ),
        Button(Const('Ok'), id='pay_ok', on_click=send_pay_check),
        Back(Const('Назад')),
        state=BalanceSG.pay_photo,
        getter=balance_getter
    ),
    Window(
        Const(text='Готово'),
        Button(Const('Главное меню'), id='go_start', on_click=go_start),
        state=BalanceSG.confirm,
    ),
)
