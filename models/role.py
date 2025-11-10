from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, ForeignKeyField


class Role(BaseModel):
    """
    角色表
    """
    id = IntegerField()
    role_name = CharField()
    describe = CharField()
    route_id = CharField()
    is_del = IntegerField()



    class Meta:
        table_name = 'lv_role'

    @classmethod
    def create_role(cls, role_name: str, describe: str,):
        return Role.create(role_name=role_name, describe=describe,is_del=0)

    @classmethod
    def update_role_info(cls, id: int, role_name: str, describe: str):
        return Role.update(role_name=role_name, describe=describe).where(Role.id == id).execute()
    @classmethod
    def update_role_route(cls, id: int, route_id: str):
        return Role.update(route_id=route_id).where(Role.id == id).execute()

    @classmethod
    def single_by_id(cls, id: int):
        db = Role.undelete().select().where(Role.id == id)
        return db.first()

    @classmethod
    def single_by_role_name(cls, role_name: str):
        db = Role.select().where(Role.is_del == 0)

        if role_name != '':
            db = db.where(Role.role_name == role_name)
        return db.first()


    @classmethod
    def single_by_id_role_name(cls, id: int, role_name: str):
        db = Role.select().where(Role.id != id).where(Role.role_name == role_name)
        return db.first()

    #删除角色
    @classmethod
    def delete_role(cls, id: List[int]):
        return Role.update(is_del=1).where(Role.id.in_(id)).execute()


    #获取所有记录
    @classmethod
    def all_list(cls):
        return Role.undelete().select().where(Role.is_del == 0).order_by(Role.id.asc()).dicts()




    @classmethod
    def fetch_all(cls, page: int = 1, page_size: int = 10):
        db = Role.undelete().select().where(Role.is_del == 0)

        role_list, paginate = paginator(db, page, page_size, "id asc")

        return role_list, paginate
