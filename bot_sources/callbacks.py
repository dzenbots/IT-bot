from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from settings import CHANNEL_ID
from . import bot, logger, get_unauthorized_user_start_message, get_rm_group_keyboard, \
    keyboard_to_chose_users_groups, user_info, get_main_inline_keyboard, get_start_keyboard, main_movement_keyboard, \
    get_edit_equipment_keyboard, get_kurpus_keyboard_for_create_movement, is_person
from models import User, Links, Group, Equipment


@bot.callback_query_handler(func=lambda call: call.data == 'Groups-list')
def show_group_list(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Admins'):
            raise Exception("Unauthorized user")
    except Exception:
        bot.send_message(text=get_unauthorized_user_start_message(), chat_id=call.message.chat.id)
        return
    groups = Group.select()
    return_str = 'Список групп:\n'
    for group in groups:
        return_str += group.group_name + '\n'
    bot.edit_message_text(text=return_str, chat_id=call.message.chat.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'ADD-group')
def add_group(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Admins'):
            raise Exception("Unauthorized user")
    except Exception:
        bot.send_message(text=get_unauthorized_user_start_message(), chat_id=call.message.chat.id)
        return
    User.update(status='Adding group').where(User.id == user.id).execute()
    bot.edit_message_text(text='Введите название новой группы пользователей',
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'RM-group')
def show_groups_for_remove(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Admins'):
            raise Exception("Unauthorized user")
    except Exception:
        bot.send_message(text=get_unauthorized_user_start_message(), chat_id=call.message.chat.id)
        return
    User.update(status=f'rm_group').where(User.id == user.id).execute()
    bot.edit_message_text(text='Выберите группу для удаления',
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          reply_markup=get_rm_group_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'rm-group')
def remove_group(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Admins'):
            raise Exception("Unauthorized user")
    except Exception:
        bot.send_message(text=get_unauthorized_user_start_message(), chat_id=call.message.chat.id)
        return

    links = Links.select(Links).join(Group).where(Group.id == int(call.data.split('_')[1]))
    for link in links:
        link.delete_instance()
    logger.info(f"remove group - {Group.get(id=int(call.data.split('_')[1])).group_name}")
    group = Group.get(id=int(call.data.split('_')[1]))
    group.delete_instance()
    groups = Group.select()
    return_str = 'Список групп:\n'
    for group in groups:
        return_str += group.group_name + '\n'
    bot.edit_message_text(text=return_str, chat_id=call.message.chat.id, message_id=call.message.message_id)
    User.update(status='').where(User.id == user.id).execute()


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'add-user-to-group')
def add_user_to_group(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Admins'):
            raise Exception("Unauthorized user")
    except Exception:
        bot.send_message(text=get_unauthorized_user_start_message(), chat_id=call.message.chat.id)
        return
    temp_user = User.get(User.id == int(call.data.split('_')[1]))
    temp_user_groups = Group.select(Group).join(Links).where(Links.user == temp_user.id)
    all_groups = Group.select()
    reply_keyboard = InlineKeyboardMarkup()
    for group in all_groups:
        if group not in temp_user_groups:
            reply_keyboard.row(
                InlineKeyboardButton(text=group.group_name,
                                     callback_data=f'group-to-add-user_{group.id}_{temp_user.id}'))
    bot.edit_message_text(
        text=f'В какую группу необходимо добавить пользователя {temp_user.first_name} {temp_user.last_name}',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=reply_keyboard)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'group-to-add-user')
def group(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Admins'):
            raise Exception("Unauthorized user")
    except Exception:
        bot.send_message(text=get_unauthorized_user_start_message(), chat_id=call.message.chat.id)
        return
    group_to_add_to = Group.get(id=int(call.data.split('_')[1]))
    user_to_be_entered_to_group = User.get(id=int(call.data.split('_')[2]))
    Links.get_or_create(user=user_to_be_entered_to_group,
                        group=group_to_add_to)
    if user_to_be_entered_to_group in User.select(User).join(Links).join(Group).where(
            Group.group_name == 'Unauthorized'):
        temp_link = Links.get(user=user_to_be_entered_to_group,
                              group=Group.get(group_name='Unauthorized'))
        temp_link.delete_instance()
    logger.info(
        f'{user.first_name} {user.last_name} added user {user_to_be_entered_to_group.first_name} {user_to_be_entered_to_group.last_name} to group {group_to_add_to.group_name}')
    bot.send_message(chat_id=user_to_be_entered_to_group.telegram_id,
                     text=f'Вы авторизованы и добавлены в группу {group_to_add_to.group_name}',
                     reply_markup=get_start_keyboard(user))
    bot.send_message(chat_id=user_to_be_entered_to_group.telegram_id,
                     text='Список доступных Вам функций',
                     reply_markup=get_main_inline_keyboard(user_to_be_entered_to_group))
    bot.edit_message_text(message_id=call.message.message_id,
                          chat_id=call.message.chat.id,
                          text=user_info(user_to_be_entered_to_group),
                          reply_markup=keyboard_to_chose_users_groups(user_to_be_entered_to_group))


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'rm-user-from-group')
def rm_user_from_group(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Admins'):
            raise Exception("Unauthorized user")
    except Exception:
        bot.send_message(text=get_unauthorized_user_start_message(), chat_id=call.message.chat.id)
        return
    temp_user = User.get(User.id == int(call.data.split('_')[1]))
    temp_user_groups = Group.select(Group).join(Links).where(Links.user == temp_user.id)
    all_groups = Group.select()
    reply_keyboard = InlineKeyboardMarkup()
    for group in all_groups:
        if group in temp_user_groups:
            reply_keyboard.row(
                InlineKeyboardButton(text=group.group_name,
                                     callback_data=f'group-to-remove-user_{group.id}_{temp_user.id}'))
    bot.edit_message_text(
        text=f'Из какой группы необходимо удалить пользователя {temp_user.first_name} {temp_user.last_name}',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=reply_keyboard)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'group-to-remove-user')
def group(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Admins'):
            raise Exception("Unauthorized user")
    except Exception:
        bot.send_message(text=get_unauthorized_user_start_message(), chat_id=call.message.chat.id)
        return
    group_to_remove_from = Group.get(id=int(call.data.split('_')[1]))
    user_to_be_removed_from_group = User.get(id=int(call.data.split('_')[2]))
    Links.get(user=user_to_be_removed_from_group,
              group=group_to_remove_from).delete_instance()
    logger.info(
        f'{user.first_name} {user.last_name} removed user {user_to_be_removed_from_group.first_name} {user_to_be_removed_from_group.last_name} from group {group_to_remove_from.group_name}')
    bot.send_message(chat_id=user_to_be_removed_from_group.telegram_id,
                     text=f'Вы удалены из группы {group_to_remove_from.group_name}',
                     reply_markup=get_start_keyboard(user))
    bot.send_message(chat_id=user_to_be_removed_from_group.telegram_id,
                     text='Список доступных Вам функций',
                     reply_markup=get_main_inline_keyboard(user_to_be_removed_from_group))
    if Group.select(Group).join(Links).join(User).where(User.id == user_to_be_removed_from_group.id).count() == 0:
        Links.get_or_create(user=user_to_be_removed_from_group,
                            group=Group.get(group_name='Unauthorized'))
        bot.send_message(chat_id=user_to_be_removed_from_group.telegram_id,
                         text='Вы были удалены из всех групп. Получите авторизацию у администратора, чтобы продолжить пользоваться этим ботом!',
                         reply_markup=None)
    bot.edit_message_text(message_id=call.message.message_id,
                          chat_id=call.message.chat.id,
                          text=user_info(user_to_be_removed_from_group),
                          reply_markup=keyboard_to_chose_users_groups(user_to_be_removed_from_group))


@bot.callback_query_handler(func=lambda call: call.data == 'check_equipment')
def check_equipment_zavhoz(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Zavhoz'):
            raise Exception("Unauthorized user")
    except Exception:
        logger.info(
            f'User {user.first_name} {user.last_name} tried to check equipment, but this user is not in Zavhoz group!')
        bot.send_message(text='У Вас нет доступа к этой функции', chat_id=call.message.chat.id)
        return
    bot.send_message(chat_id=user.telegram_id,
                     text='Введите инвентарный номер оборудования')
    User.update(status='zavhoz_check_equipment').where(User.telegram_id == user.telegram_id).execute()


@bot.callback_query_handler(func=lambda call: call.data == 'move_equipment')
def start_movement(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            raise Exception("Unauthorized user")
    except Exception:
        logger.info(
            f'User {user.first_name} {user.last_name} tried to use inventarization functions, but this user is not in Inventarization group!')
        bot.send_message(text='У Вас нет доступа к этой функции', chat_id=call.message.chat.id)
        return
    bot.edit_message_text(chat_id=user.telegram_id,
                          text='Параметр поиска оборудования:',
                          reply_markup=main_movement_keyboard,
                          message_id=call.message.message_id)
    User.update(status='main_search').where(User.id == user.id).execute()


@bot.callback_query_handler(func=lambda call: call.data == 'main_invent_search')
def main_invent_search(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            raise Exception("Unauthorized user")
    except Exception:
        logger.info(
            f'User {user.first_name} {user.last_name} tried to use inventarization functions, but this user is not in Inventarization group!')
        bot.send_message(text='У Вас нет доступа к этой функции', chat_id=call.message.chat.id)
        return
    bot.edit_message_text(chat_id=user.telegram_id,
                          message_id=call.message.message_id,
                          text='Введите инвентарный номер')
    User.update(status='invent_search').where(User.id == user.id).execute()


@bot.callback_query_handler(func=lambda call: call.data == 'main_serial_search')
def main_serial_search(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            raise Exception("Unauthorized user")
    except Exception:
        logger.info(
            f'User {user.first_name} {user.last_name} tried to use inventarization functions, but this user is not in Inventarization group!')
        bot.send_message(text='У Вас нет доступа к этой функции', chat_id=call.message.chat.id)
        return
    bot.edit_message_text(chat_id=user.telegram_id,
                          message_id=call.message.message_id,
                          text='Введите серийный номер')
    User.update(status='serial_search').where(User.id == user.id).execute()


@bot.callback_query_handler(func=lambda call: call.data.split('-')[0] == 'edit_info')
def start_edit_equipment(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            raise Exception("Unauthorized user")
    except Exception:
        logger.info(
            f'User {user.first_name} {user.last_name} tried to use inventarization functions, but this user is not in Inventarization group!')
        bot.send_message(text='У Вас нет доступа к этой функции', chat_id=call.message.chat.id)
        return
    equipment = Equipment.get(id=int(call.data.split('-')[1]))
    bot.send_message(chat_id=user.telegram_id,
                     text='Выберите параметр для редактирования',
                     reply_markup=get_edit_equipment_keyboard(equipment))
    User.update(status='choose parameter for edit').where(User.id == user.id).execute()


@bot.callback_query_handler(func=lambda call: call.data.split('/')[0] == 'edit')
def start_edit_equipment(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            raise Exception("Unauthorized user")
    except Exception:
        logger.info(
            f'User {user.first_name} {user.last_name} tried to use inventarization functions, but this user is not in Inventarization group!')
        bot.send_message(text='У Вас нет доступа к этой функции', chat_id=call.message.chat.id)
        return
    equipment = Equipment.get(id=int(call.data.split('-')[1]))
    field_name = call.data.split('/')[1].split('-')[0]
    if field_name == 'type':
        bot.edit_message_text(chat_id=user.telegram_id,
                              message_id=call.message.message_id,
                              text='Введите новое наименование типа')
        User.update(status=f'edit-type_{equipment.id}').where(User.id == user.id).execute()
    elif field_name == 'mark':
        bot.edit_message_text(chat_id=user.telegram_id,
                              message_id=call.message.message_id,
                              text='Введите новое наименование марки')
        User.update(status=f'edit-mark_{equipment.id}').where(User.id == user.id).execute()
    elif field_name == 'model':
        bot.edit_message_text(chat_id=user.telegram_id,
                              message_id=call.message.message_id,
                              text='Введите новое наименование модели')
        User.update(status=f'edit-model_{equipment.id}').where(User.id == user.id).execute()
    elif field_name == 'serial':
        bot.edit_message_text(chat_id=user.telegram_id,
                              message_id=call.message.message_id,
                              text='Введите новый серийный номер')
        User.update(status=f'edit-serial_{equipment.id}').where(User.id == user.id).execute()


@bot.callback_query_handler(func=lambda call: call.data.split('-')[0] == 'move_equipment')
def start_moving_equipment(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            raise Exception("Unauthorized user")
    except Exception:
        logger.info(
            f'User {user.first_name} {user.last_name} tried to use inventarization functions, but this user is not in Inventarization group!')
        bot.send_message(text='У Вас нет доступа к этой функции', chat_id=call.message.chat.id)
        return
    equipment = Equipment.get(id=int(call.data.split('-')[1]))
    bot.send_message(chat_id=user.telegram_id,
                     text='Выберите корпус для перемещения',
                     reply_markup=get_kurpus_keyboard_for_create_movement(equipment))


@bot.callback_query_handler(func=lambda call: call.data.split('-')[0] == 'choose_room')
def start_moving_equipment(call):
    if not is_person(call.message.chat):
        return
    try:
        user = User.get(telegram_id=call.message.chat.id)
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'Inventarization'):
            raise Exception("Unauthorized user")
    except Exception:
        logger.info(
            f'User {user.first_name} {user.last_name} tried to use inventarization functions, but this user is not in Inventarization group!')
        bot.send_message(text='У Вас нет доступа к этой функции', chat_id=call.message.chat.id)
        return
    campus = call.data.split('-')[1].split('UK')[1]
    equipment = Equipment.get(id=int(call.data.split('-')[2]))
    bot.edit_message_text(message_id=call.message.message_id,
                          chat_id=user.telegram_id,
                          text='Введите кабинет для перемещения')
    User.update(status=f'create_movement/UK-{campus}/id-{equipment.id}').where(User.id == user.id).execute()
