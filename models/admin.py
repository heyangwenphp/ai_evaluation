from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, ForeignKeyField

from models.role import Role


class Admin(BaseModel):
    """
    管理员表
    """
    id = IntegerField(primary_key=True, sequence=True)
    username = CharField()
    password = CharField()
    state = IntegerField()
    # role = IntegerField()
    role_id = ForeignKeyField(Role, backref='admin')
    is_del = IntegerField()

    class Meta:
        table_name = 'lv_admin'
        database = BaseModel._meta.database

    @classmethod
    def create_admin(cls, username: str, password: str, state: int = 1, role_id: int = 1):
        return Admin.create(username=username, password=password, state=state, role_id=role_id, is_del=0)

    @classmethod
    def update_admin(cls, id: int, username: str, password: str, state: int = 1, role_id: int = 1):
        if password == '':
            return Admin.update(username=username, state=state, role_id=role_id).where(Admin.id == id).execute()
        else:
            return Admin.update(username=username, password=password, state=state, role_id=role_id).where(
                Admin.id == id).execute()

    @classmethod
    def update_state(cls, id: int, state: int):
        return Admin.update(state=state).where(Admin.id == id).execute()

    @classmethod
    def single_by_id(cls, uid: int):
        return Admin.undelete().select().join(Role).where(Admin.id == uid).first()

    @classmethod
    def single_by_username(cls, username: str):
        db = Admin.select().where(Admin.is_del == 0)

        if username != '':
            db = db.where(Admin.username == username)
        return db.first()
        # if db:
        #     return model_to_dict(db)

    @classmethod
    def single_by_id_username(cls, id: int, username: str):
        db = Admin.select().where(Admin.id != id).where(Admin.username == username)
        return db.first()

    # 删除
    @classmethod
    def delete_user(cls, id: int):
        return Admin.update(is_del=1).where(Admin.id == id).execute()

    @classmethod
    def fetch_all(cls, page: int = 1, page_size: int = 10):
        db = Admin.select(Admin.id, Admin.username, Admin.state, Admin.role_id, Admin.createTime, Admin.updateTime,
                          Role.role_name, Role.is_del.alias('role_is_del')).join(Role, attr='role').where(Admin.is_del == 0)

        admin_list, paginate = paginator(db, page, page_size, "updateTime desc")

        return admin_list, paginate

