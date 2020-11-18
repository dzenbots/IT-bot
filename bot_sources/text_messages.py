from telebot.types import Message

from models import User, Group, Links, Equipment, Movement, Person
from bot_sources import bot, logger, get_unauthorized_user_start_message, get_main_inline_keyboard, equipment_info, \
    get_equipment_reply_markup, send_equipment_info_to_google_sheet, send_movement_to_google_sheet, is_person, \
    get_person_info, get_contact_reply_markup


@bot.message_handler(func=lambda message: message.text == 'На главную')
def go_main(message: Message):
    if not is_person(message.chat):
        return
    try:
        user = User.get(telegram_id=message.chat.id)
        if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Unauthorized'):
            raise Exception("Unauthorized user")
    except Exception:
        bot.send_message(text=get_unauthorized_user_start_message(), chat_id=message.chat.id)
        return
    bot.send_message(text="Список доступных Вам функций:", chat_id=message.chat.id,
                     reply_markup=get_main_inline_keyboard(user))


# @bot.message_handler(func=lambda message: message.text == 'Пост в канал')
# def channel_post(message: Message):
#     if not is_person(message.chat):
#         return
#     try:
#         user = User.get(telegram_id=message.chat.id)
#         if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Admins'):
#             raise Exception("Unauthorized user")
#     except Exception:
#         bot.send_message(text=get_unauthorized_user_start_message(), chat_id=message.chat.id)
#         return
#     bot.send_message(text="<b>Test</b> <i>1234</i>", chat_id=CHANNEL_URL, parse_mode='html')
#     # bot.send_media_group(chat_id=CHANNEL_URL, media=[InputMediaPhoto()])


@bot.message_handler(content_types=['text'])
def plain_text(message: Message):
    if not is_person(message.chat):
        return
    try:
        user = User.get(telegram_id=message.chat.id)
        if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Unauthorized'):
            raise Exception("Unauthorized user")
    except Exception:
        bot.send_message(text=get_unauthorized_user_start_message(), chat_id=message.chat.id)
        return

    if user.status == 'Adding group':
        if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Admins'):
            group, created = Group.get_or_create(group_name=message.text)
            bot.send_message(chat_id=message.chat.id, text='Группа добавлена')
            groups = Group.select()
            return_str = 'Список групп:\n'
            for group in groups:
                return_str += group.group_name + '\n'
            bot.send_message(text=return_str, chat_id=message.chat.id)
            logger.info(f'Admin {user.first_name} {user.last_name} add new group - {message.text}')

    elif user.status == 'zavhoz_check_equipment':
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Zavhoz'):
            bot.send_message(chat_id=user.telegram_id,
                             text='У Вас нет доступа к этой функции')
            logger.info(f'User {user.first_name} {user.last_name} had unsupported status!')
        else:
            looking_invent_num = message.text
            try:
                Equipment.get(invent_num=looking_invent_num)
            except Exception as e:
                logger.info(
                    f'User {user.first_name} {user.last_name} looking for unexisting equipment with {looking_invent_num} invent number')
                bot.send_message(chat_id=user.telegram_id,
                                 text=f'Оборудование с инвентарным номером {looking_invent_num} не стоит на балансе')
                User.update(status='').where(User.id == user.id).execute()
                return
            found_equipments = Equipment.select().where(Equipment.invent_num == looking_invent_num)
            for item in found_equipments:
                bot.send_message(chat_id=user.telegram_id,
                                 text=equipment_info(equipment=item))
            logger.info(f'User {user.first_name} {user.last_name} looked info about {looking_invent_num} invent number')

    elif user.status == 'invent_search':
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            bot.send_message(chat_id=user.telegram_id,
                             text='У Вас нет доступа к этой функции')
            logger.info(f'User {user.first_name} {user.last_name} had unsupported status!')
        else:
            invent_num = message.text
            found_equipments = Equipment.select().where(Equipment.invent_num == invent_num)
            if found_equipments.count() == 0:
                bot.send_message(chat_id=user.telegram_id,
                                 text=f'Оборудование с инвентарным номером {invent_num} не стоит на балансе')
            else:
                for equipment in found_equipments:
                    bot.send_message(chat_id=user.telegram_id,
                                     text=equipment_info(equipment),
                                     reply_markup=get_equipment_reply_markup(equipment))

    elif user.status == 'serial_search':
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            bot.send_message(chat_id=user.telegram_id,
                             text='У Вас нет доступа к этой функции')
            logger.info(f'User {user.first_name} {user.last_name} had unsupported status!')
        else:
            serial_num = message.text
            found_equipments = Equipment.select().where(Equipment.serial_num == serial_num)
            if found_equipments.count() == 0:
                bot.send_message(chat_id=user.telegram_id,
                                 text=f'Оборудование с серийным номером {serial_num} не стоит на балансе')
            else:
                for equipment in found_equipments:
                    bot.send_message(chat_id=user.telegram_id,
                                     text=equipment_info(equipment),
                                     reply_markup=get_equipment_reply_markup(equipment))

    elif user.status.split('_')[0] == 'edit-type':
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            bot.send_message(chat_id=user.telegram_id,
                             text='У Вас нет доступа к этой функции')
            logger.info(f'User {user.first_name} {user.last_name} had unsupported status!')
        else:
            equipment = Equipment.get(id=user.status.split('_')[1])
            Equipment.update(type=message.text).where(Equipment.id == equipment.id).execute()
            equipment = Equipment.get(id=user.status.split('_')[1])
            bot.send_message(chat_id=user.telegram_id,
                             text=equipment_info(equipment),
                             reply_markup=get_equipment_reply_markup(equipment))
            send_equipment_info_to_google_sheet(equipment)
            logger.info(
                f'User {user.first_name} {user.last_name} edit equipment ID {equipment.it_id}: new type is {equipment.type}')
    elif user.status.split('_')[0] == 'edit-mark':
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            bot.send_message(chat_id=user.telegram_id,
                             text='У Вас нет доступа к этой функции')
            logger.info(f'User {user.first_name} {user.last_name} had unsupported status!')
        else:
            equipment = Equipment.get(id=user.status.split('_')[1])
            Equipment.update(mark=message.text).where(Equipment.id == equipment.id).execute()
            equipment = Equipment.get(id=user.status.split('_')[1])
            bot.send_message(chat_id=user.telegram_id,
                             text=equipment_info(equipment),
                             reply_markup=get_equipment_reply_markup(equipment))
            send_equipment_info_to_google_sheet(equipment)
            logger.info(
                f'User {user.first_name} {user.last_name} edit equipment ID {equipment.it_id}: new mark is {equipment.mark}')
    elif user.status.split('_')[0] == 'edit-model':
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            bot.send_message(chat_id=user.telegram_id,
                             text='У Вас нет доступа к этой функции')
            logger.info(f'User {user.first_name} {user.last_name} had unsupported status!')
        else:
            equipment = Equipment.get(id=user.status.split('_')[1])
            Equipment.update(model=message.text).where(Equipment.id == equipment.id).execute()
            equipment = Equipment.get(id=user.status.split('_')[1])
            bot.send_message(chat_id=user.telegram_id,
                             text=equipment_info(equipment),
                             reply_markup=get_equipment_reply_markup(equipment))
            send_equipment_info_to_google_sheet(equipment)
            logger.info(
                f'User {user.first_name} {user.last_name} edit equipment ID {equipment.it_id}: new model is {equipment.model}')
    elif user.status.split('_')[0] == 'edit-serial':
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            bot.send_message(chat_id=user.telegram_id,
                             text='У Вас нет доступа к этой функции')
            logger.info(f'User {user.first_name} {user.last_name} had unsupported status!')
        else:
            equipment = Equipment.get(id=user.status.split('_')[1])
            Equipment.update(serial_num=message.text).where(Equipment.id == equipment.id).execute()
            equipment = Equipment.get(id=user.status.split('_')[1])
            bot.send_message(chat_id=user.telegram_id,
                             text=equipment_info(equipment),
                             reply_markup=get_equipment_reply_markup(equipment))
            send_equipment_info_to_google_sheet(equipment)
            logger.info(
                f'User {user.first_name} {user.last_name} edit equipment ID {equipment.it_id}: new serial num is {equipment.serial_num}')
    elif user.status.split('/')[0] == 'create_movement':
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            bot.send_message(chat_id=user.telegram_id,
                             text='У Вас нет доступа к этой функции')
            logger.info(f'User {user.first_name} {user.last_name} had unsupported status!')
        else:
            campus = user.status.split('/')[1].split('-')[1]
            room = message.text
            equipment = Equipment.get(id=user.status.split('/')[2].split('-')[1])
            movement = Movement.create(equipment=equipment,
                                       campus=f'УК {campus}',
                                       room=room)
            equipment = Equipment.get(id=user.status.split('/')[2].split('-')[1])
            bot.send_message(chat_id=user.telegram_id,
                             text=equipment_info(equipment),
                             reply_markup=get_equipment_reply_markup(equipment))
            send_movement_to_google_sheet(equipment, movement)
            logger.info(
                f'User {user.first_name} {user.last_name} move equipment ID {equipment.it_id}: new location is {movement.campus} {movement.room}')
    elif user.status.split('/')[1] == 'phone_search':
        search_parameter = user.status.split('/')[0]
        template = message.text
        founded_persons = None
        if search_parameter == 'surname':
            founded_persons = Person.select().where(Person.surname == template)
        elif search_parameter == 'name':
            founded_persons = Person.select().where(
                Person.name == template.split(' ')[0] and Person.patronymic == template.split(' ')[1])
        elif search_parameter == 'number':
            founded_persons = Person.select().where(Person.phone == template)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'PhonesAdmin'):
            founded_persons = founded_persons.where(Person.actual == 'True')
        if founded_persons is not None:
            for person in founded_persons:
                bot.send_message(chat_id=message.chat.id,
                                 text=get_person_info(person),
                                 reply_markup=get_contact_reply_markup(user, person))
        else:
            bot.send_message(chat_id=message.chat.id,
                             text='Я никого не нашел по введенным Вами данным')

    else:
        bot.send_message(chat_id=message.chat.id,
                         text='Воспользуйтесь кнопками или командами (/help) для выбора функции')
    User.update(status='').where(User.id == user.id).execute()
