from unittest import TestCase
from unittest.mock import patch, Mock

from bot import Bot


class Test1(TestCase):
    def test_run(self):
        count = 5
        obj = {'a': 1}
        events = [obj] * count # [obj, obj, ...]
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count