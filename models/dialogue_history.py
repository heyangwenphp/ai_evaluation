from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, TextField, ForeignKeyField, FloatField

from models.admin import Admin


class DialogueHistory(BaseModel):
    """
    对话历史表
    """
    id = IntegerField(primary_key=True, sequence=True)
    question_id = IntegerField() #对话问题id
    cases = IntegerField() #案例 0主观题 1 客观题
    content = CharField() #内容
    file_name = CharField() #文件名称
    path = CharField() #文件路径
    role = IntegerField() #对话角色 0系统 1 用户
    is_del = IntegerField() #是否删除 0否 1是


    class Meta:
        table_name = 'lv_dialogue_history'



    @classmethod
    def get_dialogue_history_id(cls, id: str):
        db = DialogueHistory.select().where(cls.id == id).where(cls.is_del == 0)
        return db.first()


    # 删除对话
    @classmethod
    def del_dialogue_history(cls, file_id: int):
        return DialogueHistory.update(is_del=1).where(cls.id == file_id).execute()





