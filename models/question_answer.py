from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, TextField, ForeignKeyField, FloatField

from models.admin import Admin


class QuestionAnswer(BaseModel):
    """
    题目回答表
    """
    id = IntegerField(primary_key=True, sequence=True)
    question_id = IntegerField() #对话问题id
    cases = IntegerField() #案例 0主观题 1 客观题
    dimension = CharField() #维度
    question_bank_id = IntegerField() #问题id
    models_id = IntegerField() #模型id
    answer_content = CharField() #回答内容
    score = FloatField() #分数
    full_mark = FloatField() #总分
    according = CharField() #打分标准
    is_del = IntegerField() #是否删除 0否 1是


    class Meta:
        table_name = 'lv_question_answer'



    @classmethod
    def get_question_answer_id(cls, id: str):
        db = QuestionAnswer.select().where(cls.id == id).where(cls.is_del == 0)
        return db.first()


    # 删除对话
    @classmethod
    def del_question_answer(cls, file_id: int):
        return QuestionAnswer.update(is_del=1).where(cls.id == file_id).execute()





