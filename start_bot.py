import time

from bot_sources import bot, logger
from models import initialize_db, Movement, Person

if __name__ == "__main__":
    initialize_db()
    # Movement.drop_table()
    # Person.drop_table()
    while True:
        try:
            bot.polling(none_stop=False, interval=0, timeout=20)
        except Exception as e:
            logger.error(e)
            time.sleep(15)
