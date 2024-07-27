# -*- coding: utf-8 -*-

from pony.orm import Database, Required, Json

import settings


db = Database()
db.bind(**settings.DATABASE_CONFIG)


class UserState(db.Entity):
    """
    Состояние пользователя внутри сценария.
    """

    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class Registration(db.Entity):
    """
    Заявки на регистрацию.
    """

    name = Required(str)
    email = Required(str)


db.generate_mapping(create_tables=True)
