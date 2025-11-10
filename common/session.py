
import math
import datetime

from peewee import Model, ModelSelect, SQL, DateTimeField, MySQLDatabase
from contextvars import ContextVar
from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import ReconnectMixin

from core.config import settings

db_state_default = {"closed": None, "conn": None, "ctx": None, "transactions": None}
db_state = ContextVar("db_state", default=db_state_default.copy())


# reference to https://fastapi.tiangolo.com/advanced/sql-databases-peewee/#context-variable-sub-dependency
# class PeeweeConnectionState(_ConnectionState):
#     def __init__(self, **kwargs):
#         super().__setattr__("_state", db_state)
#         super().__init__(**kwargs)
#
#     def __setattr__(self, name, value):
#         self._state.get()[name] = value
#
#     def __getattr__(self, name):
#         return self._state.get()[name]
#
#
# db = PooledMySQLDatabase(
#     settings.MYSQL_DATABASE,
#     max_connections=1000,
#     stale_timeout=30,
#     user=settings.MYSQL_USERNAME,
#     host=settings.MYSQL_HOST,
#     password=settings.MYSQL_PASSWORD,
#     port=settings.MYSQL_PORT
# )
#
# db._state = PeeweeConnectionState()

class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


db = ReconnectMySQLDatabase(
    settings.MYSQL_DATABASE,
    user=settings.MYSQL_USERNAME,
    host=settings.MYSQL_HOST,
    password=settings.MYSQL_PASSWORD,
    port=settings.MYSQL_PORT,
    charset='utf8mb4'
)



class BaseModel(Model):
    #deleted_at = DateTimeField()
    # createTime = DateTimeField(default=datetime.datetime.now())
    # updateTime = DateTimeField(default=datetime.datetime.now())
    createTime = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updateTime = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])

    @classmethod
    def undelete(cls):
        # for logic delete
        return cls.select()

    class Meta:
        database = db


def paginator(query: ModelSelect, page: int, page_size: int, order_by: str = "id ASC"):
    count = query.count()
    if page < 1:
        page = 1

    if page_size <= 0:
        page_size = 10

    if page_size >= 100:
        page_size = 100

    if page == 1:
        offset = 0
    else:
        offset = (page - 1) * page_size

    query = query.offset(offset).limit(page_size).order_by(SQL(order_by))

    total_pages = math.ceil(count / page_size)

    paginate = {
        "total_pages": total_pages,
        "count": count,
        "current_page": page,
        "pre_page": page - 1 if page > 1 else page,
        "next_page": page if page == total_pages else page + 1
    }

    return list(query.dicts()), paginate
