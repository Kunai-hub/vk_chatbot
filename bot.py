# -*- coding: utf-8 -*-

import logging
import random

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from pony.orm import db_session

import handlers
from models import UserState, Registration

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

    @db_session
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
        state = UserState.get(user_id=str(user_id))

        if state is not None:
            self.continue_scenario(text=text, state=state, user_id=user_id)
        else:
            for intent in settings.INTENTS:
                log.debug(f'Пользователь получил {intent}')
                if any(token in text.lower() for token in intent['tokens']):
                    if intent['answer']:
                        self.send_text(text_to_send=intent['answer'], user_id=user_id)
                    else:
                        self.start_scenario(user_id=user_id, scenario_name=intent['scenario'], text=text)
                    break
            else:
                self.send_text(text_to_send=settings.DEFAULT_ANSWER, user_id=user_id)

    def start_scenario(self, user_id, scenario_name, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_step(step=step, user_id=user_id, text=text, context={})
        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})

    def continue_scenario(self, text, state, user_id):
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]
        handler = getattr(handlers, step['handler'])

        if handler(text=text, context=state.context):
            next_step = steps[step['next_step']]
            self.send_step(step=next_step, user_id=user_id, text=text, context=state.context)
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                log.info('Пользователь {name} {email} успешно прошёл регистрацию.'.format(**state.context))
                Registration(name=state.context['name'], email=state.context['email'])
                state.delete()
        else:
            text_to_send = step['failure_text'].format(**state.context)
            self.send_text(text_to_send=text_to_send, user_id=user_id)

    def send_step(self, step, user_id, text, context):
        if 'text' in step:
            self.send_text(text_to_send=step['text'].format(**context), user_id=user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text=text, context=context)
            self.send_image(image_to_send=image, user_id=user_id)

    def send_text(self, text_to_send, user_id):
        self.get_api.messages.send(
            message=text_to_send,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def send_image(self, image_to_send, user_id):
        pass # TODO


if __name__ == '__main__':
    configure_logging()
    bot = Bot(group_id=settings.GROUP_ID, token=settings.TOKEN)
    bot.run()
