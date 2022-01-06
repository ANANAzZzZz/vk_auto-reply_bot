from simple_bot import Bot

from scheduled_bot import Scheduled_bot

from longpoll_bot import LongPollBot


# Simple Bot

"""
# создание и запуск обычного бота
bot = Bot()

# отправка тестового сообщения
bot.send_message(receiver_user_id="221132552", message_text="Привет, это сообщение отправлено автоматически")
"""

# Scheduled Bot

"""
# создание и запуск бота, отправляющего сообщения по расписанию
scheduledBot = Scheduled_bot()
"""

# LongPoll Bot

# создание и запуск бота, автоматически отвечающего на заданные сообщения
long_poll_bot = LongPollBot()
long_poll_bot.run_long_poll()
