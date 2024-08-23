from aiogram.fsm.state import StatesGroup, State


class StartSG(StatesGroup):
    start = State()
    contacts = State()
    date_select = State()
    fio = State()
    tel = State()
    guests = State()
    end = State()


class NewDialog(StatesGroup):
    question = State()
    result = State()


class AddCarSG(StatesGroup):
    """
    6️⃣
    7️⃣
    8️⃣
    9️⃣
    1️⃣
    0️⃣"""
    start = State()
    marka = State()
    model = State()
    year = State()
    kpp = State()
    probeg = State()
    price = State()
    tel = State()
    descr = State()
    photo = State()
    confirm = State()
    finish = State()


class ProfileSG(StatesGroup):
    start = State()
    balance = State()


class BalanceSG(StatesGroup):
    start = State()
    balance = State()
    pay_photo = State()
    confirm = State()