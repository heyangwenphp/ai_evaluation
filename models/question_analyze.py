from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, TextField, ForeignKeyField, FloatField

from models.admin import Admin


class QuestionAnalyze(BaseModel):
    """
    分析表
    """
    id = IntegerField(primary_key=True, sequence=True)
    question_id = IntegerField() #对话问题id
    analysis_results = TextField() #分析结果，JSON格式
    is_del = IntegerField() #是否删除 0否 1是


    class Meta:
        table_name = 'lv_question_analyze'



    @classmethod
    def get_analyze_by_question_id(cls, question_id: int):
        db = QuestionAnalyze.select().where(cls.question_id == question_id).where(cls.is_del == 0)
        return db.first()








