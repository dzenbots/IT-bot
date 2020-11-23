from telebot.types import Message

from bot_sources import bot, logger, is_person, get_unauthorized_user_start_message, get_person_info, \
    get_contact_reply_markup, update_person_info_in_google
from models import User, Links, Group, Person


@bot.message_handler(content_types=['photo'])
def receive_photo(message: Message):
    if not is_person(message.chat):
        return
    try:
        user = User.get(telegram_id=message.chat.id)
        if user in User.select(User).join(Links).join(Group).where(Group.group_name == 'Unauthorized'):
            raise Exception("Unauthorized user")
    except Exception:
        bot.send_message(text=get_unauthorized_user_start_message(user=user), chat_id=message.chat.id)
        return
    if user.status.split(':')[0] == 'Edit_person_info':
        if user not in User.select(User).join(Links).join(Group).where(Group.group_name == 'PhonesAdmin'):
            bot.send_message(chat_id=user.telegram_id,
                             text='У Вас нет доступа к этой функции')
            logger.info(f'User {user.first_name} {user.last_name} had unsupported status!')
        else:
            edit_parameter = user.status.split(':')[1].split('_')[0]
            if not edit_parameter == 'photo':
                return
            else:
                photo_id = message.photo[0].file_id
                person = Person.get(id=user.status.split(':')[1].split('_')[1])
                Person.update(photo=f'{str(photo_id)}').where(Person.id == person.id).execute()
                User.update(status='').where(User.id == user.id).execute()
                if not person.photo == '':
                    bot.send_photo(chat_id=message.chat.id,
                                   photo=person.photo,
                                   caption=get_person_info(person),
                                   reply_markup=get_contact_reply_markup(user, person))
                else:
                    bot.send_message(chat_id=message.chat.id,
                                     text=get_person_info(person),
                                     reply_markup=get_contact_reply_markup(user, person))
                bot.send_contact(chat_id=message.chat.id,
                                 phone_number=person.phone,
                                 first_name=person.surname,
                                 last_name=f"{person.name} {person.patronymic}")
                person = Person.get(id=user.status.split(':')[1].split('_')[1])
                update_person_info_in_google(person)
