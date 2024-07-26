# -*- coding: utf-8 -*-

from pony.orm import Database, Required
from psycopg2.extensions import JSON

import settings


db = Database()
db.bind(**settings.DATABASE_CONFIG)


class UserState(db.Entity):
    scenrio_name = Required(str)
    step_name = Required(str)
    context = Required(JSON)
