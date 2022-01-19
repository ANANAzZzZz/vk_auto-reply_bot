from longpoll_bot import LongPollBot

from sklearn.feature_extraction.text import TfidfVectorizer # для векторизации текста
from sklearn.linear_model import LogisticRegression # для классификации намерений
from vk_api.longpoll import VkEventType # использование событий vk
import zipfile # для распаковки архива датасета с диалогами
import os.path # для проверки наличия файла
import random # для генерации случайных ответов
import nltk # библиотека для естественной обработки языка
import json # представление в качестве JSON


class NLULongPollBot(LongPollBot):
    """
    Бот, прослушивающий в бесконечном цикле входящие сообщения и способный отвечать на них
    Бот обучен на заданном конфиге и открытом датасете с диалогами (могут быть погрешности в ответах)
    """

    # векторизатор текста
    vectorizer = None

    # классификатор запросовъ
    classifier = None

    # датасет на основе открытых диалогов
    dataset = {} # {слово: [[запрос, ответ], [запрос 2, ответ 2], ...], ...}

    # порог вероятности, при котором на намерение пользователя будет отправляться ответ из bot_config
    threshold = 0.7

    # ведение статистки ответов
    stats = {"intent": 0, "generative": 0, "failure": 0}

    # конфигурация бота с намерениями действия, примерами запросов и ответов на них (можно обойтись без нее)

    bot_config = {
        "intents": {
            "hello": {
                "examples": ["Привет", "Здравствуйте", "Добрый день"],
                "responses": ["Привет", "Здравствуй"]
            },
            "bye": {
                "examples": ["Пока", "До свидания", "Увидимся"],
                "responses": ["Пока"]
            },
        },

        "failure_phrases": [
            "Не знаю, что сказать даже",
            "Меня не научили отвечать на такое",
            "Я не знаю, как отвечать на такое"
        ]
    }

    def __init__(self):
        """
        иниациализация бота
        """

        super().__init__()

        # загрузка конфига из файла
        with open("bot_corpus/bot_config.json", encoding="utf-8") as file:
            self.bot_config = json.load(file)

        self.create_bot_config_corpus()
        self.create_bot_dialog_dataset()


    def run_long_poll(self):
        """
        Запуск бота
        """
        print("Запуск бота")

        for event in self.long_poll.listen():

            # если пришло новое сообщение - происходит проверка текста сообщения
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:

                # ответ отправляется в личные сообщения пользователю (если сообщение из личного чата)
                if event.from_user:

                    # получение ответа бота с последующей отправкой его пользователю
                    bot_respone = self.get_bot_response(event.text)
                    self.send_message(receiver_user_id=event.user_id, message_text=bot_respone)

                    # вывод логов
                    print(self.stats)


    def get_bot_response(self, request: str):
        """
        Отправка ответа пользователю на его запрос с учетом статистики
        :param request: запрос пользователя
        :return: ответ для пользователя
        """

        # определение намерения пользователя,
        # использование заготовленного ответа из конфига
        intent = self.get_intent(request)
        if intent:
            self.stats["intent"] += 1
            return self.get_response_by_intent(intent)

        # если нет заготовленного ответа - идет поиск ответа в датасете диалогов
        response = self.get_generative_response(request)
        if response:
            self.stats["generative"] += 1
            return response

        # если бот не может подобрать ответ - отпровляется ответ-заглушка
        self.stats["failure"] += 1
        return self.get_failure_phrase()


    def get_intent(self, request: str):
        """
        получение наиболее вероятного намерения пользователя из сообщения
        :param request: запрос пользователя
        :return: наилучшее совпадение
        """

        question_probabilities = self.classifier.predict_proba(self.vectorizer.transform([request]))[0]
        best_intent_probability = max(question_probabilities)

        if best_intent_probability > self.threshold:
            best_intent_index = list(question_probabilities).index(best_intent_probability)
            best_intent = self.classifier.classes_[best_intent_index]
            return best_intent

        return None


    def get_response_by_intent(self, intent: str):
        """
        получение случайного ответа на намерение пользователя
        :param intent: намерение пользователя
        :return: случайный ответ из прописанных для намерения
        """

        phrases = self.bot_config["intents"][intent]["responses"]
        return random.choice(phrases)


    def normalize_request(self, request):
        """
        Приведение запроса пользователя к нормальному виду путем избавления от лишних символов и смены регистра
        :param request: запрос пользователя
        :return: запрос пользователя в нижнем регистре без спец-символов
        """

        normalized_request = request.lower().strip()
        alphabet = " -1234567890йцукенгшщзхъфывапролджэёячсмитьбю"
        normalized_request = "".join(character for character in normalized_request if character in alphabet)
        return normalized_request


    def get_generative_response(self, request: str):
        """
        Подбор ответа, получаемого из открытого датасета
        :param request: запрос пользователя
        :return: ответ из датасета диалогов
        """

        phrase = self.normalize_request(request)
        words = phrase.split(" ")

        mini_dataset = []
        for word in words:
            if word in self.dataset:
                mini_dataset += self.dataset[word]

        candidates = []

        for question, answer in mini_dataset:
            if abs(len(question) - len(request)) / len(question) < 0.4:
                distance = nltk.edit_distance(question, request)
                score = distance / len(question)
                if score < 0.4:
                    candidates.append([question, answer, score])

        if candidates:
            return min(candidates, key=lambda candidate: candidate[0])[1]

        return None

    def get_failure_phrase(self):
        """
        Если бот не может ничего ответить, будет отправлена случайная фраза из списка failure_phrases в bot_config
        :return: случайная фраза, в случае провала подбора ответа ботом
        """

        phrases = self.bot_config["failure_phrases"]
        return random.choice(phrases)

    def create_bot_config_corpus(self):
        """
        Создание и обучение корпуса для бота, обученного на bot_config для дальнейшей обработки запросов пользователя
        """

        corpus = []
        y = []

        for intent, intent_data in self.bot_config["intents"].items():
            for example in intent_data["examples"]:
                corpus.append(example)
                y.append(intent)

        # векторизация
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 3))
        x = self.vectorizer.fit_transform(corpus)

        # классификация
        self.classifier = LogisticRegression()
        self.classifier.fit(x, y)

        print("обучение на файле конфигурации завершено")

    def create_bot_dialog_dataset(self):
        """
        Загрузка датасета диалогов для чат-бота путем парсинга файла
        Открытые датасеты диалогов для обучения бота: https://github.com/Koziev/NLP_Datasets
        Можно использовать выгрузку истории сообщений из собстенных диалогов ВКонтакте в таком же виде
        """

        if not os.path.isfile("bot_corpus/dialogues.txt"):
            with zipfile.ZipFile("bot_corpus/dialogues.zip", "r") as zip_file:
                zip_file.extractall("bot_corpus")
                print("Распаковка датасета завершена")

        with open("bot_corpus/dialogues.txt", encoding="utf-8") as file:
            content = file.read()

        dialogues = content.split("\n\n")
        questions = set()

        for dialogue in dialogues:
            phrases = dialogue.split("\n")[:2]
            if len(phrases) == 2:
                question, answer = phrases
                question = self.normalize_request(question[2:])
                answer = answer[2:]

                if question and question not in questions:
                    questions.add(question)
                    words = question.split(" ")
                    for word in words:
                        if word not in self.dataset:
                            self.dataset[word] = []
                        self.dataset[word].append([question, answer])

        too_popular = set()
        for word in self.dataset:
            if len(self.dataset[word]) > 10000:
                too_popular.add(word)

        for word in too_popular:
            self.dataset.pop(word)

        print("Загрузка датасета диалогов завершена")
