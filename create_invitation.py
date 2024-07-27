# -*- coding: utf-8 -*-

from PIL import Image, ImageDraw, ImageFont


BASE_PATH = 'files_data/temp_invitation.jpeg'

FONT_PATH = 'files_data/georgia.ttf'
FONT_SIZE = 25
FONT_COLOR = (0, 0, 0)

NAME_OFFSET = (270, 298)
EMAIL_OFFSET = (270, 350)


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

    base.show()
