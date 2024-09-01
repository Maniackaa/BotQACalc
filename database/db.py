import dataclasses
import datetime
import pickle

from aiogram.enums import ContentType
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import create_engine, ForeignKey, String, DateTime, \
    Integer, select, delete, Text, BLOB, JSON
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database


# db_url = f"postgresql+psycopg2://{conf.db.db_user}:{conf.db.db_password}@{conf.db.db_host}:{conf.db.db_port}/{conf.db.database}"
from config.bot_settings import BASE_DIR, logger, settings

db_path = BASE_DIR / 'db.sqlite3'
db_url = f"sqlite:///{db_path}"
engine = create_engine(db_url, echo=False)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    def set(self, key, value):
        _session = Session(expire_on_commit=False)
        with _session:
            if isinstance(value, str):
                value = value[:999]
            setattr(self, key, value)
            _session.add(self)
            _session.commit()
            logger.debug(f'Изменено значение {key} на {value}')
            return self


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    tg_id: Mapped[str] = mapped_column(String(30), unique=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    register_date: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=True)
    fio: Mapped[str] = mapped_column(String(200), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer(), default=0)
    balance: Mapped[int] = mapped_column(Integer(), default=150)
    objs: Mapped[list['ObjModel']] = relationship(back_populates='user', lazy='subquery')

    def __repr__(self):
        return f'{self.id}. {self.username or "-"} {self.tg_id}'


class ObjModel(Base):
    __tablename__ = 'objmodels'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    user: Mapped['User'] = relationship(back_populates='objs', lazy='subquery')
    created: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(tz=settings.tz))
    text: Mapped[str] = mapped_column(String(4000))
    photos: Mapped[str] = mapped_column(JSON())
    channel: Mapped[str] = mapped_column(String(30))
    target_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    posted_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    def get_media_group(self):
        media_group = MediaGroupBuilder(caption=self.text)
        for photo in self.photos:
            media_group.add_photo(media=photo)
        return media_group.build()

    def __str__(self):
        return f'{self.__class__.__name__}({self.id})'


if not database_exists(db_url):
    create_database(db_url)
Base.metadata.create_all(engine)

marks = ['Toyota', 'Лада', 'Volkswagen', 'Nissan', 'Kia', 'Hyundai', 'Honda', 'Mutsubishi', 'Mercedes-Benz', 'BMW', 'Mazda', 'Ford', 'Chevrolet', 'Renault', 'Lexus', 'Subaru', 'Audi', 'Skoda', 'Opel', 'Chery', 'УАЗ', 'ЛУАЗ', 'ГАЗ', 'ТагАЗ', 'Suzuki', 'Haval', 'Land Rover', 'Peugeot', 'Daewoo', 'Infiniti', 'Gelly', 'Exeed', 'Volvo', 'Daihatsu', 'Citroen', 'Ssang Yong', 'Porsche', 'Lifan', 'Omoda', 'Jeep', 'ЗАЗ', 'Datsun', 'Great Wall', 'Changan', 'МОСКВИЧ', 'Cadilac', 'Fiat', 'Dodge', 'Mini', 'Genesis', 'ИЖ', 'Jaguar', 'Chrysler', 'Isuzu', 'Evolute', 'FAW', 'Smart', 'Vortex', 'Acura', 'Tesla', 'Hummer', 'JAC', 'SEAT', 'Ravon', 'Lincoln', 'Dongfeng', 'BYD']
price = {
    'Platinum 10мм': 10000,
    'Premium KR 7мм': 10000,
    'Platinum KR 10мм': 10000,
    'Brilliance 12мм': 10000,
    'Prime 7мм': 10000,
    'Prime 10мм': 10000,
    'Luxury 20мм': 10000,
    'Luxury 15мм': 10000,
}
colors = ['Черный', 'Темно-серый', 'Коричневый', 'Бежевый', 'Серый', 'Синий']
steps_group = {
    1: {'start': 3, 'end': 9},
    2: {'start': 38, 'end': 42},
    3: {'start': 44, 'end': 46},

}
questions = {
    1: {'q': 'Введите телефон клиента', 'a': [], 'variable_answer': True},
    2: {'q': 'Введите модель авто или выберите из вариантов', 'a': marks, 'variable_answer': True},
    # Коврики
    3: {'q': 'Какие коврики нужны? (выберите или введите свой вариант)', 'variable_answer': True,
        'a': ['Комплект ковриков', 'Передние коврики', 'Коврик в багажник', 'Водительский коврик', 'Задние коврики']},
    4: {'q': 'Выберите комплектацию ковриков или введите свой вариант?', 'a': price.keys(), 'variable_answer': True},
    5: {'q': 'Выберите цвет материала?', 'a': colors, 'variable_answer': True},
    6: {'q': 'Введите количество комплектов', 'a': [], 'variable_answer': True, 'check_func': float},
    7: {'q': 'Введите стоимость комплекта', 'a': [], 'variable_answer': True, 'check_func': float},
    8: {'q': 'Нужен комментарий (если да, укажите)?', 'a': ['Нет'], 'variable_answer': True},
    9: {'q': 'Добавить еще комлпект?', 'a': ['Да', 'Нет']},
    # Детали конфигурации и опции
    10: {'q': 'Выберите тип язычка', 'a': ['Без язычка', '2D', '3D']},
    11: {'q': 'Введите кол-во язычков', 'a': [], 'check_func': float},
    12: {'q': 'Введите стоимость язычка', 'a': [], 'variable_answer': True, 'check_func': float},
    13: {'q': 'Нужен комментарий (если да, укажите)?', 'a': ['Нет'], 'variable_answer': True},
    14: {'q': 'Выберите тип перемычки', 'a': ['Без перемычки', '2D', '3D', 'Сплошной задний коврик', '3D цельный']},
    15: {'q': 'Введите кол-во перемычек', 'a': [], 'check_func': float},
    16: {'q': 'Введите стоимость перемычки', 'a': [], 'variable_answer': True, 'check_func': float},
    17: {'q': 'Нужен комментарий (если да, укажите)?', 'a': ['Нет'], 'variable_answer': True},
    18: {'q': 'Выберите тип подпятника', 'a': ['Без подпятника', 'Экокожи', 'Текстильный', 'Текстильный сменный', 'Металлический', 'Резиновый']},
    19: {'q': 'Введите кол-во подпятников', 'a': ['1'], 'check_func': float},
    20: {'q': 'Введите стоимость подпятника', 'a': [], 'variable_answer': True, 'check_func': float},
    21: {'q': 'Нужен комментарий (если да, укажите)?', 'a': ['Нет'], 'variable_answer': True},
    # Окантовка
    22: {'q': 'Выберите тип окантовки ковриков или введите свой вариант?', 'a': ['Экокожи с подгибкой', 'Экокожи', 'Алькантара', 'Оверлок', 'Текстильная']},
    23: {'q': 'Выберите цвет окантовки?', 'a': colors, 'variable_answer': True},
    24: {'q': 'Выберите тип прострочки окантовки?', 'a': ['Одинарная', 'Двойная']},
    25: {'q': 'Выберите цвет нитки окантовки или введите свой вариант?', 'a': colors, 'variable_answer': True},
    26: {'q': 'Выберите цвет внутренней нитки окантовки или введите свой вариант?', 'a': colors, 'variable_answer': True},
    27: {'q': 'Выберите цвет внешней нитки окантовки или введите свой вариант?', 'a': colors, 'variable_answer': True},
    28: {'q': 'Есть ли микрокант?', 'a': ['Да', 'Нет']},
    29: {'q': 'Выберите цвет микроканта?', 'a': colors, 'variable_answer': True},
    30: {'q': 'Введите количество комплектов', 'a': [], 'variable_answer': True, 'check_func': float},
    31: {'q': 'Введите стоимость комплекта окантовки', 'a': [], 'variable_answer': True, 'check_func': float},
    32: {'q': 'Нужен комментарий (если да, укажите)?', 'a': ['Нет'], 'variable_answer': True},
    # Вышивки и другие опции
    33: {'q': 'Нужны ли вышивки?', 'a': ['Да', 'Нет']},
    34: {'q': 'Выберите кол-во вышивок', 'a': ['1', '2', '3', '4'], 'variable_answer': True, 'check_func': float},
    35: {'q': 'Введите стоимость 1й вышивки', 'a': [], 'variable_answer': True, 'check_func': float},
    36: {'q': 'Нужен комментарий (если да, укажите)?', 'a': ['Нет'], 'variable_answer': True},
    # Опции
    37: {'q': 'Нужны ли дополнительные опции?', 'a': ['Да', 'Нет']},
    38: {'q': 'Введите название дополнительной опции', 'a': [], 'variable_answer': True},
    39: {'q': 'Введите кол-во опции', 'a': [], 'variable_answer': True, 'check_func': float},
    40: {'q': 'Введите стоимость опции за шт', 'a': [], 'variable_answer': True, 'check_func': float},
    41: {'q': 'Нужен комментарий (если да, укажите)?', 'a': ['Нет'], 'variable_answer': True},
    42: {'q': 'Нужны ли еще дополнительные опции?', 'a': ['Да', 'Нет']},
    # Фото
    43: {'q': 'Прикрепить фото?', 'a': ['Да', 'Нет']},
    44: {'q': 'Отправьте изображение', 'q_content_type': ContentType.PHOTO},
    45: {'q': 'Введите комментарий к фотографии  (если да, укажите)?', 'a': ['Нет'], 'variable_answer': True},
    46: {'q': 'Прикрепить еще фото?', 'a': ['Да', 'Нет']},
    47: {'q': 'Введите процент скидки', 'a': ['0', '5'], 'check_func': float, 'variable_answer': True},

}

def get_podpyatnik_price(name: str):
    result = 0 if name == 'Без подпятника' else 2000
    return result

def get_yazik_count(name: str):
    result = 0 if name == 'Без язычка' else 1
    return result


def get_peremichka_count(name: str):
    result = 0 if name == 'Без перемычки' else 1
    return result


def get_yazik_price(name: str):
    result = 0 if name == 'Без язычка' else 2000
    return result


def get_count(name: str):
    logger.debug(f'get_count {name}')
    result = 1
    values = questions[3]['a'] # Какие коврики нужны?
    logger.debug(values)
    if name in [values[1], values[4]]:
        result = 0.6
    if name == values[3]:
        result = 0.3
    logger.debug(f'Объем материала: {result}')
    return result


def get_price(name: str):
    result = price.get(name, 0)
    return result



