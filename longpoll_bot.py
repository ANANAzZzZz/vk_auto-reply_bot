from simple_bot import Bot

from vk_api.longpoll import VkLongPoll, VkEventType


class LongPollBot(Bot):
    """
    Бот, прослушивающий в бесконечном цикле входящие сообщения и способный отвечать на некоторые из них
    Бот отвечает на строго заданные сообщения
    """

    # длительное подключение
    long_poll = None


    def __init__(self):
        """
        инициализация бота
        """

        super().__init__()
        self.long_poll = VkLongPoll(self.vk_session)

        print("Бот запущен")

    def run_long_poll(self):
        """
        Запуск бота
        """

        for event in self.long_poll.listen():
            # если пришло новое сообщение - происходит проверка его текста
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:

                # если была получена одна из заданных фрах
                if event.text == "Привет" or event.text == "привет" or event.text == "Здравствуй" or event.text == "здравствуй":

                    # ответ отправляется в личные сообщения пользователя (если сообщение пришло из личного чата)
                    if event.from_user:
                        self.send_message(receiver_user_id=event.user_id, message_text="И тебе привет")

                    # ответ отправляется в беседу (если сообщение было получено в общем чате)
                    elif event.from_chat:
                        self.send_message(receiver_user_id=event.chat_id, message_text="Привет")