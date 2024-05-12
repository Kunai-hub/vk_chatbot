import random
from _token import token
import vk_api
import vk_api.bot_longpoll

group_id = 225880064


class Bot:
    def __init__(self, group_id, token):
        self.group_id = group_id
        self.token = token
        self.vk_api = vk_api.VkApi(token=token)
        self.long_poller = vk_api.bot_longpoll.VkBotLongPoll(self.vk_api, self.group_id)
        self.get_api = self.vk_api.get_api()

    def run(self):
        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception as e:
                print(e)

    def on_event(self, event):
        if event.type == vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW:
            self.get_api.messages.send(
                message=event.object['message']['text'],
                random_id=random.randint(0, 2 ** 20),
                peer_id=event.object['message']['peer_id'],
            )
        else:
            print('Мы пока не умеем обрабатывать событие такого типа', event.type)


if __name__ == '__main__':
    bot = Bot(group_id=group_id, token=token)
    bot.run()