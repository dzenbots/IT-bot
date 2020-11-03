from loguru import logger
from telebot import TeleBot, apihelper
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from GoogleSheetsAPI import GoogleSync
from models import User, Group, Links, Equipment, Movement
from settings import BOT_TOKEN, BOT_PROXY, LOG_FILE

logger.add(LOG_FILE)

apihelper.proxy = BOT_PROXY
bot = TeleBot(token=BOT_TOKEN, num_threads=4)


def get_unauthorized_user_start_message():
    return f"""Вы не авторизованный пользователь!
Дождитесь пока администратор разрешит Вам использование данного бота!"""


def user_info(user: User):
    groups_str = ""
    for item in Group.select(Group).join(Links).join(User).where(User.id == user.id):
        groups_str += item.group_name + ' '
    return f"""Информация о пользователе:
    ID: {user.telegram_id}
    FName: {user.first_name}
    LName: {user.last_name}
    Groups: {groups_str}"""


def get_new_unauthorized_user_message(user: User):
    return f"""Новая попытка подключения
{user_info(user)}"""


def get_start_keyboard(user: User):
    start_keyboard = ReplyKeyboardMarkup(True)
    start_keyboard.row('На главную')
    return start_keyboard


def get_main_inline_keyboard(user: User):
    ret_keyboard = InlineKeyboardMarkup()
    if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Zavhoz'):
        ret_keyboard.row(InlineKeyboardButton(text='Проверить расположение оборудования',
                                              callback_data='check_equipment'))
    if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
        ret_keyboard.row(InlineKeyboardButton(text='Поиск и перемещение оборудования',
                                              callback_data='move_equipment'))
    if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Users'):
        ret_keyboard.row(InlineKeyboardButton(text='Телефонный справочник',
                                              callback_data='phone_number_search'))
    return ret_keyboard


main_movement_keyboard = InlineKeyboardMarkup()
main_movement_keyboard.row(InlineKeyboardButton(text='Инвентарный номер', callback_data='main_invent_search'))
main_movement_keyboard.row(InlineKeyboardButton(text='Сарийный номер', callback_data='main_serial_search'))

groups_keyboard = InlineKeyboardMarkup()
groups_keyboard.row(InlineKeyboardButton(text='Показать список всех групп', callback_data='Groups-list'))
groups_keyboard.row(InlineKeyboardButton(text='Добавить группу', callback_data='ADD-group'))
groups_keyboard.row(InlineKeyboardButton(text='Удалить группу', callback_data='RM-group'))

inventarization_inline_keyboard = InlineKeyboardMarkup()
inventarization_inline_keyboard.row(InlineKeyboardButton(text='По инвентарному номеру'),
                                    InlineKeyboardButton(text='По серийному номеру'))


def get_rm_group_keyboard():
    groups = Group.select()
    rm_group_keyboard = InlineKeyboardMarkup()
    for group in groups:
        rm_group_keyboard.row(InlineKeyboardButton(text=group.group_name, callback_data=f'rm-group_{group.id}'))
    return rm_group_keyboard


def get_admin_help_message():
    return f"""
/all_users_info - информация о подключившихся пользователях
/groups - работа с группами
/google_update - получить изменения из таблицы"""


def keyboard_to_chose_users_groups(user: User):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton(text='Добавить в группу', callback_data=f'add-user-to-group_{user.id}'),
                 InlineKeyboardButton(text='Удалить из группы', callback_data=f'rm-user-from-group_{user.id}'))
    return keyboard


def equipment_info(equipment: Equipment):
    ret_str = 'Информация об оборудовании\n'
    ret_str += f'ID: {equipment.it_id}\n'
    ret_str += f'Инвентарный номер: {equipment.invent_num}\n'
    ret_str += f'Тип: {equipment.type}\n'
    ret_str += f'Марка: {equipment.mark}\n'
    ret_str += f'Модель: {equipment.model}\n'
    ret_str += f'Серийный номер: {equipment.serial_num}\n\n'
    try:
        movements = Movement.select().where(Movement.equipment == equipment)
        movement = None
        for item in movements:
            movement = item
        ret_str += f'Корпус: {movement.campus}\n'
        ret_str += f'Кабинет: {movement.room}\n'
    except:
        ret_str += 'Корпус: N/A\n'
        ret_str += 'Кабинет: N/A\n'
    return ret_str


def send_equipment_info_to_google_sheet(equipment: Equipment):
    GoogleSync().write_data_to_range(list_name='Список оборудования',
                                     range_in_list=f'A{equipment.id + 1}:G{equipment.id + 1}',
                                     data=[[
                                         str(equipment.it_id),
                                         str(equipment.pos_in_buh),
                                         str(equipment.invent_num),
                                         str(equipment.type),
                                         str(equipment.mark),
                                         str(equipment.model),
                                         str(equipment.serial_num)
                                     ]])


def send_movement_to_google_sheet(equipment: Equipment, movement: Movement):
    GoogleSync().write_data_to_range(list_name='Перемещение оборудования',
                                     range_in_list=f'A{movement.id + 1}:G{movement.id + 1}',
                                     data=[[
                                         str(equipment.it_id),
                                         str(movement.campus),
                                         str(movement.room)
                                     ]])


def get_equipment_reply_markup(equipment: Equipment):
    ret_markup = InlineKeyboardMarkup()
    ret_markup.row(InlineKeyboardButton(text='Изменение информации',
                                        callback_data=f'edit_info-{equipment.id}'))
    ret_markup.row(InlineKeyboardButton(text='Перемещение оборудования',
                                        callback_data=f'move_equipment-{equipment.id}'))
    return ret_markup


def get_edit_equipment_keyboard(equipment: Equipment):
    edit_equipment_keyboard = InlineKeyboardMarkup()
    edit_equipment_keyboard.row(InlineKeyboardButton(text='Тип',
                                                     callback_data=f'edit/type-{equipment.id}'))
    edit_equipment_keyboard.row(InlineKeyboardButton(text='Марка',
                                                     callback_data=f'edit/mark-{equipment.id}'))
    edit_equipment_keyboard.row(InlineKeyboardButton(text='Модель',
                                                     callback_data=f'edit/model-{equipment.id}'))
    edit_equipment_keyboard.row(InlineKeyboardButton(text='Серийный номер',
                                                     callback_data=f'edit/serial-{equipment.id}'))
    return edit_equipment_keyboard


def get_kurpus_keyboard_for_create_movement(equipment: Equipment):
    ret_keyboard = InlineKeyboardMarkup()
    ret_keyboard.row(InlineKeyboardButton(text='УК 1', callback_data=f'choose_room-UK1-{equipment.id}'))
    ret_keyboard.row(InlineKeyboardButton(text='УК 2', callback_data=f'choose_room-UK2-{equipment.id}'))
    ret_keyboard.row(InlineKeyboardButton(text='УК 3', callback_data=f'choose_room-UK3-{equipment.id}'))
    ret_keyboard.row(InlineKeyboardButton(text='УК 4', callback_data=f'choose_room-UK4-{equipment.id}'))
    ret_keyboard.row(InlineKeyboardButton(text='УК 5', callback_data=f'choose_room-UK5-{equipment.id}'))
    ret_keyboard.row(InlineKeyboardButton(text='УК 6', callback_data=f'choose_room-UK6-{equipment.id}'))
    ret_keyboard.row(InlineKeyboardButton(text='УК 7', callback_data=f'choose_room-UK7-{equipment.id}'))
    ret_keyboard.row(InlineKeyboardButton(text='УК 8', callback_data=f'choose_room-UK8-{equipment.id}'))
    ret_keyboard.row(InlineKeyboardButton(text='УК 9', callback_data=f'choose_room-UK9-{equipment.id}'))
    ret_keyboard.row(InlineKeyboardButton(text='УК 10', callback_data=f'choose_room-UK10-{equipment.id}'))
    return ret_keyboard


import bot_sources.commands
import bot_sources.text_messages
import bot_sources.callbacks
