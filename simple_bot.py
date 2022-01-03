import vk_api
from vk_api.utils import get_random_id
from dotenv import load_dotenv
import os

class Bot:

    # текущия сессия vk
    vk_session = None

    # доступ к vk API
    vk_api_access = None

    # пометка авторизации
    authorised = False

    # id пользователя vk
    # (используется для ведения диалога с конкретным пользователем)
    default_user_id = None

    def __init__(self):

        # загрузка информации из .env файла
        load_dotenv()

        # авторизация
        self.vk_api_access = self.do_auth()

        if self.vk_api_access is not None:
            self.authorised = True

        # получение id пользователя из .env файла
        self.default_user_id = os.getenv("USER_ID")

    def do_auth(self):
        """
        Авторизация за пользователя (не за группу или приложение)
        Использует переменную, хранящуюся в файле настроек окружения .env в виде строки ACCESS_TOKEN
        :return: возможность работать с API
        """

        token = os.getenv("ACCESS_TOKEN")
        try:
            self.vk_session = vk_api.VkApi(token=token)
            return self.vk_session.get_api()

        except Exception as error:
            print(error)
            return None


    def send_message(self, receiver_user_id: str = None, message_text: str = "тестовое сообщение"):
        """
        Отправка сообщения от лица авторизованного пользователя
        :param receiver_user_id: уникальный идентификатор получателя сообщения
        :param message_text: текст отправляемого сообщения
        """

        if not self.authorised:
            print("Unathorised. Check if ACCESS_TOKEN is valid")
            return

        # если не указан ID - берем значение по умолчанию, если таковое указанов в .env файле
        if receiver_user_id is None:
            reciever_user_id = self.default_user_id

        try:
            self.vk_api_access.messages.send(user_id=receiver_user_id, message=message_text, random_id=get_random_id())
            print(f"Сообщение отправлено для ID {receiver_user_id} с текстом: {message_text}")
        except Exception as error:
            print(error)

