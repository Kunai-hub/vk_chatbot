# -*- coding: utf-8 -*-

import unittest
from unittest import TestCase
from unittest.mock import patch, Mock, ANY
from copy import deepcopy

from vk_api.bot_longpoll import VkBotMessageEvent
from pony.orm import db_session, rollback

import settings
from bot import Bot
from create_invitation import generate_invitation


def isolate_database(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()
    return wrapper


class Test1(TestCase):
    """
    Тесты для модуля bot.py.
    """

    RAW_EVENT = {
        'group_id': 225880064,
        'type': 'message_new',
        'event_id': '3d316509865f20e9f4292134b515919a0797ffde',
        'v': '5.199',
        'object': {
            'message': {
                'date': 1716644244,
                'from_id': 69742691,
                'id': 68,
                'out': 0,
                'version': 10000174,
                'attachments': [],
                'conversation_message_id': 68,
                'fwd_messages': [],
                'important': False,
                'is_hidden': False,
                'peer_id': 69742691,
                'random_id': 0,
                'text': 'Привет, делаю тесты'
            },
            'client_info': {
                'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link', 'callback', 'intent_subscribe',
                                   'intent_unsubscribe'],
                'keyboard': True,
                'inline_keyboard': True,
                'carousel': True,
                'lang_id': 0
            }
        }
    }

    INPUTS = [
        'Привет',
        'А когда?',
        'Где будет она проходить?',
        'Зарегистрируй меня',
        'Кирилл',
        'Моя почта email@email',
        'email@email.com'
    ]

    OUTPUTS = [
        settings.DEFAULT_ANSWER,
        settings.INTENTS[0]['answer'],
        settings.INTENTS[1]['answer'],
        settings.SCENARIOS['registration']['steps']['step_1']['text'],
        settings.SCENARIOS['registration']['steps']['step_2']['text'],
        settings.SCENARIOS['registration']['steps']['step_2']['failure_text'],
        settings.SCENARIOS['registration']['steps']['step_3']['text'].format(name='Кирилл', email='email@email.com')
    ]

    def test_run(self):
        """
        Тест на метод run.

        :return: None
        """
        count = 5
        obj = {'a': 1}
        events = [obj] * count  # [obj, obj, ...]

        # long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = Mock(return_value=events)  # = long_poller_mock

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.send_image = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count

    @isolate_database
    def test_send_message(self):
        """
        Тест на отправку сообщения по интенту или сценарию.

        :return: None
        """
        events = []
        send_mock = Mock()

        get_api_mock = Mock()
        get_api_mock.messages.send = send_mock

        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(raw=event))

        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
            bot = Bot(group_id='', token='')
            bot.get_api = get_api_mock
            bot.send_image = Mock()
            bot.run()

        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []

        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])

        assert real_outputs == self.OUTPUTS

    def test_create_invitation(self):
        """
        Тест на создание приглашения.

        :return: None
        """
        with open('files_data/Email.png', 'rb') as avatar_file:
            avatar_mock = Mock()
            avatar_mock.content = avatar_file.read()

        with patch('requests.get', return_value=avatar_mock):
            invitation_file = generate_invitation(name='Name', email='Email')

        with open('files_data/example_invitation.png', 'rb') as example_invitation_file:
            example_invitation_bytes = example_invitation_file.read()

        assert invitation_file.read() == example_invitation_bytes


if __name__ == '__main__':
    unittest.main()
