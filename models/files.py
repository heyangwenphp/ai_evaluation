from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, TextField, ForeignKeyField

from models.admin import Admin


class Files(BaseModel):
    """
    文件表
    """
    id = IntegerField(primary_key=True, sequence=True)
    user_id = IntegerField()
    file_name = CharField() #文件名称
    path = CharField() #文件路径
    suffix = CharField() #文件后缀
    is_del = IntegerField() #是否删除 0否 1是


    class Meta:
        table_name = 'lv_files'

    @classmethod
    def create_files(cls, user_id: int,file_name: str,path: str, suffix: str):
        return Files.create(user_id=user_id, file_name=file_name, path=path,suffix=suffix,is_del=0)

    @classmethod
    def get_file_id(cls, id: int):
        db = Files.select().where(cls.id == id).where(cls.is_del == 0)
        return db.first()


    # 删除文件
    @classmethod
    def del_file(cls, file_id: int):
        return Files.update(is_del=1).where(cls.id == file_id).execute()





