# -*- coding: utf-8 -*-
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont


BASE_PATH = 'files_data/temp_invitation.jpeg'

FONT_PATH = 'files_data/georgia.ttf'
FONT_SIZE = 25
FONT_COLOR = (0, 0, 0)

NAME_OFFSET = (270, 298)
EMAIL_OFFSET = (270, 350)

AVATAR_SIZE = '100x100'
AVATAR_OFFSET = (80, 290)


def generate_invitation(name, email):
    """
    Генерация приглашения на конференцию.

    :param name: имя пользователя
    :param email: email пользователя
    """

    base = Image.open(BASE_PATH).convert('RGBA')
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    draw = ImageDraw.Draw(base)
    draw.text(NAME_OFFSET, name, font=font, fill=FONT_COLOR)
    draw.text(EMAIL_OFFSET, email, font=font, fill=FONT_COLOR)

    response = requests.get(url=f'https://robohash.org/{email}?size={AVATAR_SIZE}')
    avatar_like_file = BytesIO(response.content)
    avatar = Image.open(avatar_like_file)

    base.paste(avatar, AVATAR_OFFSET)

    temp_file = BytesIO()
    base.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file
