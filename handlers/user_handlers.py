from aiogram import Router, Bot, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ErrorEvent, ReplyKeyboardRemove, CallbackQuery
from aiogram.utils.payload import decode_payload
from aiogram_dialog import DialogManager, StartMode, ShowMode

from config.bot_settings import logger
from dialogs.add_car import add_car_dialog
from dialogs.new import new_dialog
from dialogs.profile import profile_dialog, balance_dialog
from dialogs.start import start_dialog
from dialogs.states import StartSG
from services.db_func import get_or_create_user

router = Router()
router.include_router(start_dialog)
router.include_router(new_dialog)



@router.message(CommandStart(deep_link=True))
async def handler(message: Message, command: CommandObject, bot: Bot, dialog_manager: DialogManager):
    user = get_or_create_user(message.from_user)
    args = command.args
    # payload = decode_payload(args)
    logger.debug(f'payload: {args}')
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND, data={'org_key': args})


@router.message(CommandStart())
async def command_start_process(message: Message, bot: Bot, dialog_manager: DialogManager):
    user = get_or_create_user(message.from_user)
    logger.info('Старт', user=user, channel=message.chat.id)
    # await message.answer('Привет', reply_markup=start_kb)
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND)


@router.callback_query(F.data == 'start_test')
async def start_test(callback: CallbackQuery, state: FSMContext):
    user = get_or_create_user(callback.from_user)
    logger.info('Старт', user=user)



