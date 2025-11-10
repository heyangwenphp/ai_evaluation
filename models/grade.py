from typing import List
from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, DecimalField


class Grade(BaseModel):
    """
    用户等级表
    """
    id = IntegerField(primary_key=True, sequence=True)
    grade_name = CharField()
    describe = CharField()
    is_show = IntegerField()
    is_del = IntegerField()



    class Meta:
        table_name = 'lv_grade'

    @classmethod
    def create_grade(cls, grade_name: str, describe: str,is_show: int):
        return cls.create(grade_name=grade_name, describe=describe,is_show=is_show,is_del=0)






    @classmethod
    def get_grade_by_id(cls, id: int):
        db = cls.undelete().select().where(cls.id == id)
        return db.first()

    #删除角色
    @classmethod
    def delete_grade(cls, id: List[int]):
        return cls.update(is_del=1).where(cls.id.in_(id)).execute()


    #获取所有记录
    @classmethod
    def all_grade_list(cls):
        return cls.undelete().select().where(cls.is_del == 0).order_by(cls.id.asc()).dicts()




    @classmethod
    def fetch_all(cls, page: int = 1, page_size: int = 10):
        db = cls.undelete().select().where(cls.is_del == 0)
        role_list, paginate = paginator(db, page, page_size, "id asc")
        return role_list, paginate