from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, TextField, ForeignKeyField

from models.admin import Admin


class Question(BaseModel):
    """
    对话表
    """
    id = IntegerField(primary_key=True, sequence=True)
    user_id = IntegerField()
    question = CharField() #问题
    file_id = IntegerField() #文件id
    models_id = CharField() #选用的模型id
    status = IntegerField() #运行状态 0未运行 1运行中 2完成 3失败
    remarks = CharField() #备注
    is_del = IntegerField() #是否删除 0否 1是


    class Meta:
        table_name = 'lv_question'

    @classmethod
    def create_question(cls, user_id: int,question: str,file_id:int,models_id:any):
        return Question.create(user_id=user_id, question=question,file_id=file_id,models_id=models_id,is_del=0)

    @classmethod
    def get_question_id(cls, id: int):
        db = Question.select().where(cls.id == id).where(cls.is_del == 0)
        return db.first()


    # 删除对话
    @classmethod
    def del_question(cls, file_id: int):
        return Question.update(is_del=1).where(cls.id == file_id).execute()

    # 获取用户测评列表
    @classmethod
    def fetch_user_questions(cls, user_id:int,page: int = 1, page_size: int = 20):
        db = cls.select().where(cls.is_del == 0).where(cls.user_id == user_id)
        task_list, paginate = paginator(db, page, page_size, "createTime desc")

        return task_list, paginate





