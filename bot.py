import logging
import random

try:
    import settings
except ImportError:
    exit('Do cp settings.py.default settings.py and set token!')

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

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
    Echo bot для vk.com.

    Use python 3.11
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
        """Запуск бота."""
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
        if event.type == VkBotEventType.MESSAGE_NEW:
            log.debug('Отправка сообщения обратно отправителю')
            self.get_api.messages.send(
                message=event.object['message']['text'],
                random_id=random.randint(0, 2 ** 20),
                peer_id=event.object['message']['peer_id'],
            )
        else:
            log.info('Мы пока не умеем обрабатывать событие такого типа: %s', event.type)


if __name__ == '__main__':
    configure_logging()
    bot = Bot(group_id=settings.GROUP_ID, token=settings.TOKEN)
    bot.run()
