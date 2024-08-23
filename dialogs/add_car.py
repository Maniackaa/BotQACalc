import asyncio
import datetime
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
    SwitchTo, Start
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format, Const

from config.bot_settings import settings, logger


from dialogs.states import StartSG, AddCarSG
from dialogs.type_factorys import positive_int_check, tel_check
from services.db_func import create_obj, get_or_create_user
from services.email_func import send_obj_to_admin


async def car_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    data.update(dialog_manager.start_data)
    marks = ['Toyota', 'Лада', 'Volkswagen', 'Nissan', 'Kia', 'Hyundai', 'Honda', 'Mutsubishi', 'Mercedes-Benz', 'BMW', 'Mazda', 'Ford', 'Chevrolet', 'Renault', 'Lexus', 'Subaru', 'Audi', 'Skoda', 'Opel', 'Chery', 'УАЗ', 'ЛУАЗ', 'ГАЗ', 'ТагАЗ', 'Suzuki', 'Haval', 'Land Rover', 'Peugeot', 'Daewoo', 'Infiniti', 'Gelly', 'Exeed', 'Volvo', 'Daihatsu', 'Citroen', 'Ssang Yong', 'Porsche', 'Lifan', 'Omoda', 'Jeep', 'ЗАЗ', 'Datsun', 'Great Wall', 'Changan', 'МОСКВИЧ', 'Cadilac', 'Fiat', 'Dodge', 'Mini', 'Genesis', 'ИЖ', 'Jaguar', 'Chrysler', 'Isuzu', 'Evolute', 'FAW', 'Smart', 'Vortex', 'Acura', 'Tesla', 'Hummer', 'JAC', 'SEAT', 'Ravon', 'Lincoln', 'Dongfeng', 'BYD']
    kpp = ['Автоматическая', 'Механическая', 'Вариатор', 'Робот']
    car_data = {
        'marks': marks,
        'kpp': kpp
    }
    result = {}
    for key, values in car_data.items():
        items = []
        for index, item in enumerate(values):
            items.append((index, item))
        result[f'{key}_items'] = items
    data['getter'] = result
    photos = data.get('photos', [])
    photo_count = len(photos)
    result['photo_count'] = photo_count
    # logger.debug(data)
    return result


async def result_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug(f'{data}')
    return {}


async def next_window(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()


def int_check(text: str) -> str:
    if all(ch.isdigit() for ch in text) and 0 <= int(text) <= 120:
        return text
    raise ValueError


async def tel_input(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str) -> None:
    data = dialog_manager.dialog_data
    data.update(tel_input=text)
    await dialog_manager.next()


async def item_select(callback: CallbackQuery, widget: Select,
                       dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    getter = data['getter']
    field = widget.widget_id
    data[f'{field}_id'] = item_id
    data[f'{field}_str'] = getter[f'{field}_items'][int(item_id)][1]
    await dialog_manager.next()
    logger.debug(f'data: {data}')


async def text_input(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    field = widget.widget.widget_id
    data[field] = text
    await dialog_manager.next()
    logger.debug(f'data: {data}')


async def photo_handler(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager) -> None:
    # await message.send_copy(message.chat.id)
    print(message.content_type)
    data = dialog_manager.dialog_data
    photos = data.get('photos', [])
    photos.append((message.photo[-1].file_id, message.photo[-1].file_unique_id))
    photos = photos[-10:]
    data['photos'] = photos


async def on_delete(
        callback: CallbackQuery, widget: Button, dialog_manager: DialogManager,
):
    scroll: ManagedScroll = dialog_manager.find("pages")
    media_number = await scroll.get_page()
    photos = dialog_manager.dialog_data.get("photos", [])
    del photos[media_number]
    if media_number > 0:
        await scroll.set_page(media_number - 1)


async def get_photos(dialog_manager: DialogManager, event_from_user, **kwargs):
    is_admin = event_from_user.id in settings.ADMIN_IDS
    scroll: ManagedScroll = dialog_manager.find("pages")
    media_number = await scroll.get_page()
    photos = dialog_manager.dialog_data.get("photos", [])
    if photos:
        photo = photos[media_number]
        media = MediaAttachment(
            file_id=MediaId(*photo),
            type=ContentType.PHOTO,
        )
    else:
        media = MediaAttachment(
            url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Image_not_available.png/800px-Image_not_available.png?20210219185637",  # noqa: E501
            type=ContentType.PHOTO,
        )
    data = dialog_manager.dialog_data
    data['media'] = media
    mark = data.get('mark_write') or data.get('marks_str')
    model = data.get('model')
    year = data.get('year')
    kpp = data.get('kpp_str')
    probeg = data.get('probeg')
    price = data.get('price')
    tel = data.get('tel')
    descr = data.get('descr')
    text = (
        f'{mark} {model} {year} г.\n'
        f'<b>Тип КПП:</b> {kpp}\n'
        f'<b>Пробег:</b> {probeg} км.\n'
        f'<b>Цена:</b> {price} руб.\n'
        f'<b>📞Звоните:</b> <code>{tel}</code>\n'
        f'<b>Дополнительная информация:</b>\n{descr}'
    )
    data['text'] = text
    return {
        "media_count": len(photos),
        "media_number": media_number + 1,
        "media": media,
        "text1": text,
        "is_admin": is_admin
    }


async def job(bot: Bot, media_group, channel_id):
    # await asyncio.sleep(15*60)
    logger.info(f'Отправка в чат {channel_id}')
    await bot.send_media_group(chat_id=channel_id, media=media_group.build())
    logger.info('Объявление отправлено')


async def send_obj(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *args, **kwargs):
    data = dialog_manager.dialog_data
    text = data['text']
    bot = callback.bot
    logger.debug(data)
    photos = data.get('photos', [])
    photo_ids = [x[0] for x in photos]
    media_group = MediaGroupBuilder(caption=text)
    for photo in photos:
        media_group.add_photo(media=photo[0])
    channel_id = data.get('channel_id')
    # asyncio.create_task(job(bot, media_group, channel_id))
    user = get_or_create_user(callback.from_user)
    widget_id = button.widget_id
    logger.debug(widget_id)
    if widget_id == 'send_obj_now':
        delay = datetime.timedelta(minutes=0)
    else:
        delay = datetime.timedelta(minutes=15)
    now = settings.tz.localize(datetime.datetime.now())
    new_obj = create_obj(user, text=text, photos=photo_ids, channel=channel_id,
                         target_time=now + delay)
    await send_obj_to_admin(new_obj, callback.bot)
    await callback.message.answer(text='✅ Ваш пост загружен в очередь предложенных объявлений. Для ускорения отправки поста вы можете приобрести пост вне очереди - напишите сообщение @eugenesuperstar')
    await dialog_manager.done()

add_car_dialog = Dialog(
    Window(
        Format(text="""1️⃣  Выберете из списка марку автомобиля.  
Если не нашли вашу марку, напишите её текстом."""),
        Group(
            Select(Format('{item[1]}'),
                   id='marks',
                   on_click=item_select,
                   items='marks_items',
                   item_id_getter=lambda x: x[0]),
            width=4
        ),
        TextInput(
            id='mark_write',
            on_success=text_input,
        ),
        Start(Const('Назад'), state=StartSG.start, id='start_menu'),
        state=AddCarSG.marka,
        getter=car_getter,
    ),
    Window(
        Format(text='2️⃣  Напишите название модели'),
        TextInput(
            id='model',
            on_success=text_input,
        ),
        Back(Const('Назад')),
        state=AddCarSG.model,
    ),
    Window(
        Format(text='3️⃣ Год выпуска:'),
        TextInput(
            id='year',
            type_factory=positive_int_check,
            on_success=text_input,
        ),
        Back(Const('Назад')),
        state=AddCarSG.year,
    ),
    # Window(
    #     Format(text="""4️⃣ Тип КПП:"""),
    #     Column(
    #         Select(Format('{item[1]}'),
    #                id='kpp',
    #                on_click=item_select,
    #                items='kpp_items',
    #                item_id_getter=lambda x: x[0]),
    #     ),
    #     state=AddCarSG.kpp,
    #     getter=car_getter,
    # ),
    # Window(
    #     Format(text='5️⃣ Пробег:'),
    #     TextInput(
    #         id='probeg',
    #         type_factory=positive_int_check,
    #         on_success=text_input,
    #     ),
    #     Back(Const('Назад')),
    #     state=AddCarSG.probeg,
    # ),
    # Window(
    #     Format(text='6️⃣ Введите цену в Рублях:'),
    #     TextInput(
    #         id='price',
    #         type_factory=positive_int_check,
    #         on_success=text_input,
    #     ),
    #     Back(Const('Назад')),
    #     state=AddCarSG.price,
    # ),
    # Window(
    #     Format(text='7️⃣ Номер телефона:'),
    #     TextInput(
    #         id='tel',
    #         type_factory=tel_check,
    #         on_success=text_input,
    #     ),
    #     Back(Const('Назад')),
    #     state=AddCarSG.tel,
    # ),
    # Window(
    #     Format(text='8️⃣ Описание автомобиля и прочая информация:'),
    #     TextInput(
    #         id='descr',
    #         on_success=text_input,
    #     ),
    #     Back(Const('Назад')),
    #     state=AddCarSG.descr,
    # ),
    Window(
        Const(text='9️⃣ Отправьте до 10 фото, затем нажмите далее'),
        Format(text='Добавлено {photo_count} фото'),
        MessageInput(
            func=photo_handler,
            content_types=ContentType.PHOTO,
        ),
        Back(Const('Назад')),
        Next(Const('Далее')),
        state=AddCarSG.photo,
        getter=car_getter,
    ),
    Window(
        Format(text='{text1}'),
        DynamicMedia(selector="media"),
        StubScroll(id="pages", pages="media_count"),
        Group(
            NumberedPager(scroll="pages", when=F["pages"] > 1),
            width=5,
        ),
        Button(
            Format("🗑️ Удалить фото #{media_number}"),
            id="del",
            on_click=on_delete,
            when="media_count",
            # Alternative F['media_count']
        ),
        Back(Const('Назад')),
        Button(text=Const('Готово'),
               id='send_obj_btn',
               on_click=send_obj,
               when='media_count'
               ),
        # Button(text=Const('Отправить сразу'),
        #        id='send_obj_now',
        #        on_click=send_obj,
        #        when='is_admin'
        #        ),

        state=AddCarSG.confirm,
        getter=get_photos,
    ),
    # Window(
    #     Const(text='Готово'),
    #     state=AddCarSG.finish,
    #     getter=get_photos,
    # ),
)