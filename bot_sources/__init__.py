import io

from loguru import logger
from telebot import TeleBot, apihelper
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from GoogleSheetsAPI import GoogleSync
from models import User, Group, Links, Equipment, Movement, Person
from settings import BOT_TOKEN, BOT_PROXY, LOG_FILE, INVENTARIZATION_SPREADSHEET_ID, PHONE_SPREADSHEET_ID, \
    IT_SUPPORT_TABLE, IT_SUPPORT_FORM

logger.add(LOG_FILE)

apihelper.proxy = BOT_PROXY
bot = TeleBot(token=BOT_TOKEN, num_threads=4)


def is_person(chat):
    if chat.type == 'private':
        return True
    return False


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
    start_keyboard.add('На главную')
    return start_keyboard


def get_main_inline_keyboard(user: User):
    ret_keyboard = InlineKeyboardMarkup(row_width=3)
    if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Zavhoz'):
        ret_keyboard.add(InlineKeyboardButton(text=' 🔍 Проверить расположение оборудования',
                                              callback_data='check_equipment'))
    if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
        ret_keyboard.add(InlineKeyboardButton(text=' 🔍 Поиск и перемещение оборудования',
                                              callback_data='move_equipment'))
    if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Users'):
        ret_keyboard.add(InlineKeyboardButton(text=' ☎️ Телефонный справочник',
                                              callback_data='phone_number_search'))
    if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'SysAdmins'):
        ret_keyboard.add(InlineKeyboardButton(text=' 📋 Таблица заявок',
                                              url=IT_SUPPORT_TABLE))
    if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Users'):
        ret_keyboard.add(InlineKeyboardButton(text=' 🆘 Форма обращений в IT-службу',
                                              url=IT_SUPPORT_FORM))
    return ret_keyboard


main_movement_keyboard = InlineKeyboardMarkup()
main_movement_keyboard.add(InlineKeyboardButton(text='Инвентарный номер', callback_data='main_invent_search'))
main_movement_keyboard.add(InlineKeyboardButton(text='Сарийный номер', callback_data='main_serial_search'))

groups_keyboard = InlineKeyboardMarkup()
groups_keyboard.add(InlineKeyboardButton(text='Показать список всех групп', callback_data='Groups-list'))
groups_keyboard.add(InlineKeyboardButton(text='Добавить группу', callback_data='ADD-group'))
groups_keyboard.add(InlineKeyboardButton(text='Удалить группу', callback_data='RM-group'))

inventarization_inline_keyboard = InlineKeyboardMarkup()
inventarization_inline_keyboard.add(InlineKeyboardButton(text='По инвентарному номеру'),
                                    InlineKeyboardButton(text='По серийному номеру'))


def get_rm_group_keyboard():
    groups = Group.select()
    rm_group_keyboard = InlineKeyboardMarkup()
    for group in groups:
        rm_group_keyboard.add(InlineKeyboardButton(text=group.group_name, callback_data=f'rm-group_{group.id}'))
    return rm_group_keyboard


def get_user_help_message(user: User):
    ret_message = """Список доступных Вам команд:"""
    if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Admins'):
        ret_message += """
/all_users_info - информация о подключившихся пользователях
/groups - работа с группами
/google_update - получить изменения из таблицы"""
    if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'PhonesAdmin'):
        ret_message += """
/phones_update - подгрузить новые номера из таблицы"""
    return ret_message


def get_admin_help_message():
    return f"""
/all_users_info - информация о подключившихся пользователях
/groups - работа с группами
/google_update - получить изменения из таблицы"""


def keyboard_to_chose_users_groups(user: User):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Добавить в группу', callback_data=f'add-user-to-group_{user.id}'),
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
    GoogleSync(spreadsheet_id=INVENTARIZATION_SPREADSHEET_ID).write_data_to_range(list_name='Список оборудования',
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
    GoogleSync(spreadsheet_id=INVENTARIZATION_SPREADSHEET_ID).write_data_to_range(list_name='Перемещение оборудования',
                                                                                  range_in_list=f'A{movement.id + 1}:G{movement.id + 1}',
                                                                                  data=[[
                                                                                      str(equipment.it_id),
                                                                                      str(movement.campus),
                                                                                      str(movement.room)
                                                                                  ]])


def get_equipment_reply_markup(equipment: Equipment):
    ret_markup = InlineKeyboardMarkup()
    ret_markup.add(InlineKeyboardButton(text='Изменение информации',
                                        callback_data=f'edit_info-{equipment.id}'))
    ret_markup.add(InlineKeyboardButton(text='Перемещение оборудования',
                                        callback_data=f'move_equipment-{equipment.id}'))
    return ret_markup


def get_edit_equipment_keyboard(equipment: Equipment):
    edit_equipment_keyboard = InlineKeyboardMarkup()
    edit_equipment_keyboard.add(InlineKeyboardButton(text='Тип',
                                                     callback_data=f'edit/type-{equipment.id}'))
    edit_equipment_keyboard.add(InlineKeyboardButton(text='Марка',
                                                     callback_data=f'edit/mark-{equipment.id}'))
    edit_equipment_keyboard.add(InlineKeyboardButton(text='Модель',
                                                     callback_data=f'edit/model-{equipment.id}'))
    edit_equipment_keyboard.add(InlineKeyboardButton(text='Серийный номер',
                                                     callback_data=f'edit/serial-{equipment.id}'))
    return edit_equipment_keyboard


def get_kurpus_keyboard_for_create_movement(equipment: Equipment):
    ret_keyboard = InlineKeyboardMarkup()
    ret_keyboard.add(InlineKeyboardButton(text='УК 1', callback_data=f'choose_room-UK1-{equipment.id}'))
    ret_keyboard.add(InlineKeyboardButton(text='УК 2', callback_data=f'choose_room-UK2-{equipment.id}'))
    ret_keyboard.add(InlineKeyboardButton(text='УК 3', callback_data=f'choose_room-UK3-{equipment.id}'))
    ret_keyboard.add(InlineKeyboardButton(text='УК 4', callback_data=f'choose_room-UK4-{equipment.id}'))
    ret_keyboard.add(InlineKeyboardButton(text='УК 5', callback_data=f'choose_room-UK5-{equipment.id}'))
    ret_keyboard.add(InlineKeyboardButton(text='УК 6', callback_data=f'choose_room-UK6-{equipment.id}'))
    ret_keyboard.add(InlineKeyboardButton(text='УК 7', callback_data=f'choose_room-UK7-{equipment.id}'))
    ret_keyboard.add(InlineKeyboardButton(text='УК 8', callback_data=f'choose_room-UK8-{equipment.id}'))
    ret_keyboard.add(InlineKeyboardButton(text='УК 9', callback_data=f'choose_room-UK9-{equipment.id}'))
    ret_keyboard.add(InlineKeyboardButton(text='УК 10', callback_data=f'choose_room-UK10-{equipment.id}'))
    ret_keyboard.add(InlineKeyboardButton(text='Списание', callback_data=f'choose_room-UKspisanie-{equipment.id}'))
    return ret_keyboard


phone_search_parameters = InlineKeyboardMarkup()
phone_search_parameters.add(InlineKeyboardButton(text='Фамилия', callback_data='Surname_phone_search'))
phone_search_parameters.add(InlineKeyboardButton(text='Имя Отчество', callback_data='Name_phone_search'))
phone_search_parameters.add(InlineKeyboardButton(text='Телефон', callback_data='Number_phone_search'))
phone_search_parameters.add(InlineKeyboardButton(text='Классный руководитель', callback_data='KlassRuk_phone_search'))


def get_classes_table():
    ret_keyboard = InlineKeyboardMarkup()
    ret_keyboard.row(InlineKeyboardButton(text='1А', callback_data='класс_1А'),
                     InlineKeyboardButton(text='1Б', callback_data='класс_1Б'),
                     InlineKeyboardButton(text='1В', callback_data='класс_1В'),
                     InlineKeyboardButton(text='1Г', callback_data='класс_1Г'),
                     InlineKeyboardButton(text='1Д', callback_data='класс_1Д'),
                     InlineKeyboardButton(text='1М', callback_data='класс_1М'),
                     InlineKeyboardButton(text='1Н', callback_data='класс_1Н')
                     )
    ret_keyboard.row(InlineKeyboardButton(text='2А', callback_data='класс_2А'),
                     InlineKeyboardButton(text='2Б', callback_data='класс_2Б'),
                     InlineKeyboardButton(text='2В', callback_data='класс_2В'),
                     InlineKeyboardButton(text='2Г', callback_data='класс_2Г'),
                     InlineKeyboardButton(text='2Д', callback_data='класс_2Д'),
                     InlineKeyboardButton(text='2Л', callback_data='класс_2Л'),
                     InlineKeyboardButton(text='2М', callback_data='класс_2М')
                     )
    ret_keyboard.row(InlineKeyboardButton(text='3А', callback_data='класс_3А'),
                     InlineKeyboardButton(text='3Б', callback_data='класс_3Б'),
                     InlineKeyboardButton(text='3В', callback_data='класс_3В'),
                     InlineKeyboardButton(text='3Л', callback_data='класс_3Л'),
                     InlineKeyboardButton(text='3М', callback_data='класс_3М'),
                     InlineKeyboardButton(text='3У', callback_data='класс_3У')
                     )
    ret_keyboard.row(InlineKeyboardButton(text='4А', callback_data='класс_4А'),
                     InlineKeyboardButton(text='4Б', callback_data='класс_4Б'),
                     InlineKeyboardButton(text='4В', callback_data='класс_4В'),
                     InlineKeyboardButton(text='4Г', callback_data='класс_4Г'),
                     InlineKeyboardButton(text='4Л', callback_data='класс_4Л'),
                     InlineKeyboardButton(text='4М', callback_data='класс_4М'),
                     InlineKeyboardButton(text='4У', callback_data='класс_4У')
                     )
    ret_keyboard.row(InlineKeyboardButton(text='5А', callback_data='класс_5А'),
                     InlineKeyboardButton(text='5Б', callback_data='класс_5Б'),
                     InlineKeyboardButton(text='5В', callback_data='класс_5В'),
                     InlineKeyboardButton(text='5Д', callback_data='класс_5Д'),
                     InlineKeyboardButton(text='5Л', callback_data='класс_5Л'),
                     InlineKeyboardButton(text='5М', callback_data='класс_5М'),
                     InlineKeyboardButton(text='5Н', callback_data='класс_5Н')
                     )
    ret_keyboard.row(InlineKeyboardButton(text='6А', callback_data='класс_6А'),
                     InlineKeyboardButton(text='6Б', callback_data='класс_6Б'),
                     InlineKeyboardButton(text='6В', callback_data='класс_6В'),
                     InlineKeyboardButton(text='6Г', callback_data='класс_6Г'),
                     InlineKeyboardButton(text='6Д', callback_data='класс_6Д'),
                     InlineKeyboardButton(text='6Л', callback_data='класс_6Л'),
                     InlineKeyboardButton(text='6М', callback_data='класс_6М')
                     )
    ret_keyboard.row(InlineKeyboardButton(text='7А', callback_data='класс_7А'),
                     InlineKeyboardButton(text='7Б', callback_data='класс_7Б'),
                     InlineKeyboardButton(text='7Г', callback_data='класс_7Г'),
                     InlineKeyboardButton(text='7Д', callback_data='класс_7Д'),
                     InlineKeyboardButton(text='7К', callback_data='класс_7К'),
                     InlineKeyboardButton(text='7М', callback_data='класс_7М'),
                     InlineKeyboardButton(text='7Н', callback_data='класс_7Н')
                     )
    ret_keyboard.row(InlineKeyboardButton(text='8И', callback_data='класс_8И'),
                     InlineKeyboardButton(text='8К', callback_data='класс_8К'),
                     InlineKeyboardButton(text='8М', callback_data='класс_8М'),
                     InlineKeyboardButton(text='8С', callback_data='класс_8С'),
                     InlineKeyboardButton(text='8Э', callback_data='класс_8Э'),
                     InlineKeyboardButton(text='8Я', callback_data='класс_8Я')
                     )
    ret_keyboard.row(InlineKeyboardButton(text='9А', callback_data='класс_9А'),
                     InlineKeyboardButton(text='9Б', callback_data='класс_9Б'),
                     InlineKeyboardButton(text='9В', callback_data='класс_9В'),
                     InlineKeyboardButton(text='9Г', callback_data='класс_9Г'),
                     InlineKeyboardButton(text='9К', callback_data='класс_9К'),
                     InlineKeyboardButton(text='9Л', callback_data='класс_9Л'),
                     InlineKeyboardButton(text='9М', callback_data='класс_9М')
                     )
    return ret_keyboard


def get_person_info(person: Person):
    ret_str = f"""{person.surname} {person.name} {person.patronymic}
Должность: {person.position}
E-mail: {person.email}"""
    return ret_str


def get_contact_reply_markup(user: User, person: Person):
    reply_markup = None
    if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'PhonesAdmin'):
        reply_markup = InlineKeyboardMarkup()
        reply_markup.row(InlineKeyboardButton(text='Изменить',
                                              callback_data=f"Change-person_{person.id}"),
                         InlineKeyboardButton(text='Видимый ✅' if person.actual == 'True' else 'Невидимый ❌',
                                              callback_data=f"ChActual_{person.id}"))

    return reply_markup


def send_contact_info(chat_id, person: Person, user: User):
    if not person.photo == '':
        bot.send_photo(chat_id=chat_id,
                       photo=person.photo,
                       caption=get_person_info(person),
                       reply_markup=get_contact_reply_markup(user, person))
    else:
        bot.send_message(chat_id=chat_id,
                         text=get_person_info(person),
                         reply_markup=get_contact_reply_markup(user, person))
    bot.send_contact(chat_id=chat_id,
                     phone_number=person.phone,
                     first_name=person.surname,
                     last_name=f"{person.name} {person.patronymic}")
    vcf = io.StringIO()
    vcf.name = f'{person.surname} {person.name} {person.patronymic}.vcf'
    vcf.write('BEGIN:VCARD' + "\n")
    vcf.write('VERSION:3.0' + "\n")
    vcf.write('N:' + f'{person.surname};{person.name};{person.patronymic}' + "\n")
    vcf.write('ORG:' + 'ГБОУ Школа \" Дмитровский\"' + "\n")
    vcf.write('TEL;CELL:' + person.phone + "\n")
    vcf.write('EMAIL:' + person.email + "\n")
    vcf.write('END:VCARD' + "\n")
    vcf.write("\n")
    vcf.seek(0, 0)
    bot.send_document(chat_id=chat_id,
                      data=vcf,
                      caption='Для добавления контакта на Ваше устройство скачайте и откройте этот файл ⬆️')
    vcf.close()


def get_change_person_reply_markup(person: Person):
    reply_markup = InlineKeyboardMarkup(row_width=1)
    reply_markup.add(InlineKeyboardButton(text='Фамилия',
                                          callback_data=f'Edit_person-surname_{person.id}'))
    reply_markup.add(InlineKeyboardButton(text='Имя',
                                          callback_data=f'Edit_person-name_{person.id}'))
    reply_markup.add(InlineKeyboardButton(text='Отчество',
                                          callback_data=f'Edit_person-patronymic_{person.id}'))
    reply_markup.add(InlineKeyboardButton(text='Телефон',
                                          callback_data=f'Edit_person-phone_{person.id}'))
    reply_markup.add(InlineKeyboardButton(text='Фото',
                                          callback_data=f'Edit_person-photo_{person.id}'))
    reply_markup.add(InlineKeyboardButton(text='Должность',
                                          callback_data=f'Edit_person-position_{person.id}'))
    reply_markup.add(InlineKeyboardButton(text='e-mail',
                                          callback_data=f'Edit_person-email_{person.id}'))
    return reply_markup


def update_person_info_in_google(person: Person):
    GoogleSync(spreadsheet_id=PHONE_SPREADSHEET_ID).write_data_to_range(list_name='List1',
                                                                        range_in_list=f'A{person.id + 1}:G{person.id + 1}',
                                                                        data=[[
                                                                            str(person.surname),
                                                                            str(person.name),
                                                                            str(person.patronymic),
                                                                            str(person.position),
                                                                            str(person.photo),
                                                                            str(person.phone),
                                                                            str(person.email)
                                                                        ]])


import bot_sources.commands
import bot_sources.text_messages
import bot_sources.callbacks
import bot_sources.photo_messages
