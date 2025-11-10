from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, TextField, ForeignKeyField

from models.admin import Admin


class QuestionBank(BaseModel):
    """
    题目表
    """
    id = IntegerField(primary_key=True, sequence=True)
    question_id = IntegerField() #对话问题id
    cases = CharField() #案例 0主观题 1 客观题
    question = CharField() #题目
    standard_answer = CharField() #标准答案
    standard = CharField() #打分标准
    dimension = CharField() #维度
    is_del = IntegerField() #是否删除 0否 1是


    class Meta:
        table_name = 'lv_question_bank'



    @classmethod
    def get_question_bank_id(cls, id: str):
        db = QuestionBank.select().where(cls.id == id).where(cls.is_del == 0)
        return db.first()


    # 删除对话
    @classmethod
    def del_question_bank(cls, file_id: int):
        return QuestionBank.update(is_del=1).where(cls.id == file_id).execute()





