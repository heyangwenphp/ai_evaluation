import json
import random
from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, ForeignKeyField, fn


class Home(BaseModel):
    """
    home_banner表
    """
    id = IntegerField()
    cover_image = CharField()
    image = CharField()
    url = CharField()
    sort = IntegerField()
    is_del = IntegerField()



    class Meta:
        table_name = 'lv_home'



    #创建banner
    @classmethod
    def create_home(cls, cover_image: str, image: str,url:str,sort:int):
        return cls.create(cover_image=cover_image, image=image,url=url,sort=sort,is_del=0)

    #删除banner
    @classmethod
    def delete_home(cls, id: int):
        return cls.update(is_del=1).where(cls.id==id).execute()


    #获取所有记录
    @classmethod
    def all_home_list(cls):
        return cls.undelete().select().where(cls.is_del == 0).order_by(cls.sort.asc()).dicts()



