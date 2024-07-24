# -*- coding: utf-8 -*-

import logging
import random

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import handlers

try:
    import settings
except ImportError:
    exit('Do cp settings.py.default settings.py and set token!')


log = logging.getLogger('bot')
log.setLevel(logging.DEBUG)


def configure_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler('bot.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                                datefmt='%m-%d-%Y %H:%M:%S'))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)


class UserState:
    """
    Состояние пользователя внутри сценария.
    """

    def __init__(self, scenario_name, step_name, context=None):
        self.scenario_name = scenario_name
        self.step_name = step_name
        self.context = context or {}


class Bot:
    """
    Use python 3.11.

    Сценарий регистрации на конференцию для бота vk.com.
    Поддержка ответов на вопросы про дату, место проведения и сценарий регистрации:
        - спрашиваем имя
        - спрашиваем email
        - говорим об успешной регистрации
    Задаем вопросы до тех пор, пока шаг не будет пройден.
    """

    def __init__(self, group_id, token):
        """
        :param group_id: group id из группы vk.com.
        :param token: секретный токен из той же группы vk.com.
        """
        self.group_id = group_id
        self.token = token
        self.vk_api = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk_api, self.group_id)
        self.get_api = self.vk_api.get_api()
        self.user_states = dict() # user_id -> UserState

    def run(self):
        """
        Запуск бота.

        :return: None
        """
        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception:
                log.exception('Ошибка в обработке события')

    def on_event(self, event):
        """
        Отправляет сообщение назад, если это текст.

        :param event: VKBotMessageEvent object
        :return: None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info('Мы пока не умеем обрабатывать событие такого типа: %s', event.type)
            return

        user_id = event.object['message']['peer_id']
        text = event.object['message']['text']

        if user_id in self.user_states:
            text_to_send = self.continue_scenario(user_id=user_id, text=text)
        else:
            for intent in settings.INTENTS:
                log.debug(f'Пользователь получил {intent}')
                if any(token in text.lower() for token in intent['tokens']):
                    if intent['answer']:
                        text_to_send = intent['answer']
                    else:
                        text_to_send = self.start_scenario(user_id=user_id, scenario_name=intent['scenario'])
                    break
            else:
                text_to_send = settings.DEFAULT_ANSWER

        self.get_api.messages.send(
            message=text_to_send,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def start_scenario(self, user_id, scenario_name):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        text_to_send = step['text']
        self.user_states[user_id] = UserState(scenario_name=scenario_name, step_name=first_step)
        return text_to_send

    def continue_scenario(self, user_id, text):
        state = self.user_states[user_id]
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]
        handler = getattr(handlers, step['handler'])

        if handler(text=text, context=state.context):
            next_step = steps[step['next_step']]
            text_to_send = next_step['text'].format(**state.context)
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                log.info('Пользователь {name} {email} успешно прошёл регистрацию.'.format(**state.context))
                self.user_states.pop(user_id)
        else:
            text_to_send = step['failure_text'].format(**state.context)

        return text_to_send


if __name__ == '__main__':
    configure_logging()
    bot = Bot(group_id=settings.GROUP_ID, token=settings.TOKEN)
    bot.run()
