from typing import List

from common.session import BaseModel, paginator
from peewee import IntegerField, ForeignKeyField, CharField

from models.admin import Admin


class AdminLog(BaseModel):
    """
    管理员表
    """
    id = IntegerField()
    ip = CharField()
    admin_id = ForeignKeyField(Admin, backref='admin_log')
    is_del = IntegerField()

    class Meta:
        table_name = 'lv_admin_log'

    @classmethod
    def create_log(cls, admin_id: int, ip: str):
        return AdminLog.create(admin_id=admin_id, ip=ip, is_del=0)

    # 删除
    @classmethod
    def delete_log(cls, id: List[int]):
        return AdminLog.update(is_del=1).where(AdminLog.id.in_(id)).execute()

    @classmethod
    def fetch_all(cls, page: int = 1, page_size: int = 20):
        db = AdminLog.select(Admin.username, AdminLog).join(Admin, attr='admin').where(AdminLog.is_del == 0)

        admin_list, paginate = paginator(db, page, page_size, "createTime desc")

        return admin_list, paginate
