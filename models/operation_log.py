from typing import List

from common.session import BaseModel, paginator
from peewee import IntegerField, ForeignKeyField, CharField

from models.admin import Admin


class OperationLog(BaseModel):
    """
    后台操作日志表
    """
    id = IntegerField(primary_key=True, sequence=True)
    admin_id = ForeignKeyField(Admin, backref='operation_log')
    module = CharField()
    content = CharField()
    is_del = IntegerField()

    class Meta:
        table_name = 'lv_operation_log'

    @classmethod
    def create_log(cls, admin_id: int, module: str, content: str):
        return OperationLog.create(admin_id=admin_id, module=module, content=content, is_del=0)

    # 删除
    @classmethod
    def delete_log(cls, id: List[int]):
        return OperationLog.update(is_del=1).where(OperationLog.id.in_(id)).execute()

    @classmethod
    def fetch_all(cls, content: str = '', page: int = 1, page_size: int = 20):
        db = OperationLog.select(Admin.username, OperationLog).join(Admin, attr='admin').where(OperationLog.is_del == 0)
        if content:
            db = db.where(OperationLog.content.contains(content))

        admin_list, paginate = paginator(db, page, page_size, "createTime desc")

        return admin_list, paginate


