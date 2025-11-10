from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, ForeignKeyField


class RoleButton(BaseModel):
    """
    角色按钮表
    """
    id = IntegerField()
    role_id = IntegerField()
    menus_id = IntegerField()
    action = CharField()
    title = CharField()
    add = IntegerField()
    batchAdd = IntegerField()
    export = IntegerField()
    batchDelete = IntegerField()
    status = IntegerField()
    view = IntegerField()
    edit = IntegerField()
    reset = IntegerField()
    delete = IntegerField()
    shipment = IntegerField()
    role = IntegerField()
    is_del = IntegerField()

    class Meta:
        table_name = 'lv_role_button'

    @classmethod
    def create_role(cls, Item: dict):

        return RoleButton.create(role_id=Item['role_id'], menus_id=Item['menus_id'], action=Item['action'],
                                 title=Item['title'], add=Item['add'], batchAdd=Item['batchAdd'], export=Item['export'],
                                 batchDelete=Item['batchDelete'], status=Item['status'], view=Item['view'],
                                 edit=Item['edit'], reset=Item['reset'], delete=Item['delete'], shipment=Item['shipment'],
                                 role=Item['role'], is_del=0)

    @classmethod
    def update_role(cls, id: int, role_id: int, menus_id: int, action: str, title: str, add: int, batchAdd: int,
                    export: int, batchDelete: int, status: int, view: int, edit: int, reset: int, delete: int,
                    shipment: int, role: int):
        return RoleButton.update(role_id=role_id, menus_id=menus_id, action=action, title=title, add=add,
                                 batchAdd=batchAdd, export=export, batchDelete=batchDelete, status=status, view=view,
                                 edit=edit, reset=reset, delete=delete, shipment=shipment, role=role).where(
            RoleButton.id == id).execute()

    @classmethod
    def single_by_role_id(cls, role_id: int):
        return RoleButton.undelete().select().where(RoleButton.role_id == role_id).where(RoleButton.is_del == 0).dicts()

    # 删除角色
    @classmethod
    def delete_role(cls, id: List[int]):
        return RoleButton.update(is_del=1).where(RoleButton.id.in_(id)).execute()

    @classmethod
    def delete_role_id(cls, role_id: int):
        return RoleButton.update(is_del=1).where(RoleButton.role_id == role_id).execute()

    # 获取所有记录
    @classmethod
    def all_list(cls):
        return RoleButton.undelete().select().where(RoleButton.is_del == 0).order_by(RoleButton.id.asc()).dicts()
