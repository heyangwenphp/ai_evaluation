from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, TextField

import threading

class BigModels(BaseModel):
    """
    模型表
    """
    id = IntegerField(primary_key=True, sequence=True)
    title = CharField() #模型标题
    name = CharField() #模型名称
    sort = IntegerField() #排序，值越小越靠前
    types = IntegerField() #类型 0国内 1国外
    status = IntegerField() #状态 0启用 1停用
    is_del = IntegerField()


    class Meta:
        table_name = 'lv_big_models'



    @classmethod
    def get_big_models_id(cls, id: int):
        return cls.undelete().select().where(cls.id == id).first()

    @classmethod
    def get_model(cls, title: str):
        return cls.undelete().select().where(cls.title == title).first()

    @classmethod
    def get_models_list(cls):
        return cls.undelete().select(cls.id,cls.title,cls.name,cls.types).where(cls.status == 0).where(cls.is_del == 0).order_by(cls.sort.asc()).dicts()

