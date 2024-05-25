from unittest import TestCase
from unittest.mock import patch, Mock, ANY

from vk_api.bot_longpoll import VkBotMessageEvent

from bot import Bot


class Test1(TestCase):
    RAW_EVENT = {
        'group_id': 225880064, 'type': 'message_new', 'event_id': '3d316509865f20e9f4292134b515919a0797ffde',
        'v': '5.199',
        'object': {'message': {'date': 1716644244, 'from_id': 69742691, 'id': 68, 'out': 0, 'version': 10000174,
                               'attachments': [], 'conversation_message_id': 68, 'fwd_messages': [], 'important': False,
                               'is_hidden': False, 'peer_id': 69742691, 'random_id': 0, 'text': 'Привет, делаю тесты'},
                   'client_info': {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link', 'callback',
                                                      'intent_subscribe', 'intent_unsubscribe'],
                                   'keyboard': True, 'inline_keyboard': True, 'carousel': True, 'lang_id': 0}}}

    def test_run(self):
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
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count

    def test_on_event(self):
        event = VkBotMessageEvent(raw=self.RAW_EVENT)
        send_mock = Mock()

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll'):
                bot = Bot('', '')
                bot.get_api = Mock()
                bot.get_api.messages.send = send_mock

                bot.on_event(event)

        send_mock.assert_called_once_with(
            message=self.RAW_EVENT['object']['message']['text'],
            random_id=ANY,
            peer_id=self.RAW_EVENT['object']['message']['peer_id'],
        )
