from typing import List
from peewee import CharField, IntegerField, ForeignKeyField
from common.session import BaseModel, paginator
from models.users import Users


class UserColumn(BaseModel):
    """
    用户模型配置表
    """
    id = IntegerField(primary_key=True, sequence=True)
    user = ForeignKeyField(Users, backref='user_models')
    column_id = IntegerField()
    is_del = IntegerField()

    class Meta:
        table_name = 'lv_user_column'

    @classmethod
    def create_user_column(cls, user_id: int, column_id: int):
        return cls.create(user=user_id, column_id=column_id)

    @classmethod
    def get_column_user(cls,column_id:int):
        return cls.undelete().select(Users.id, Users.username, cls.createTime).join(Users, on=(
                    UserColumn.user == Users.id)).where(cls.is_del == 0).where(cls.column_id == column_id).order_by(cls.id.asc()).dicts()

    @classmethod
    def get_page_column_user(cls, keyword: str = "",column_id:int=1, page: int = 1, page_size: int = 20):
        db = cls.undelete().select(Users.id, Users.username, cls.createTime).join(Users, on=(
                    UserColumn.user == Users.id)).where(cls.is_del == 0).where(cls.column_id == column_id)
        if keyword != "":
            db = db.where(Users.username.contains(keyword))
        page_list, paginate = paginator(db, page, page_size, "createTime  desc")
        return page_list, paginate

    #获取用户模型
    @classmethod
    def get_column_scheme(cls, user_id: int,column_id: int):
        return cls.undelete().select().where(cls.user == user_id).where(cls.column_id == column_id).where(cls.is_del == 0).first()

    #栏目解绑用户
    @classmethod
    def delete_user_column(cls, user_id: List[int], column_id: int):
        return not cls.update(is_del=1).where(cls.user.in_(user_id)).where(cls.column_id == column_id).execute()
