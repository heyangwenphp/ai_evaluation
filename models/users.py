from datetime import datetime, timedelta

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, ForeignKeyField, DecimalField, JOIN

from models.grade import Grade



class Users(BaseModel):
    """
    用户表
    """
    id = IntegerField(primary_key=True, sequence=True)
    username = CharField() # 手机号
    nickname = CharField()  # 姓名
    password = CharField()
    status = IntegerField()
    grade_id = ForeignKeyField(Grade, backref='users')
    expirationTime = CharField()  # 过期时间
    is_del = IntegerField()



    class Meta:
        table_name = 'lv_users'

    @classmethod
    def create_user(cls,username: str, nickname:str,password: str,expirationTime:str):
        return cls.create(username=username,nickname=nickname, password=password, expirationTime=expirationTime,grade_id=1,status=1,is_del=0)

    @classmethod
    def single_by_id(cls, uid: str):
        db = cls.undelete().select(cls.id,cls.username,cls.nickname, cls.status, cls.grade_id,cls.expirationTime,Grade).join(Grade,attr='grade').where(Users.id == uid).where(cls.is_del == 0)
        return db.first()

    @classmethod
    def single_by_username(cls, username: str):
        return Users.select().where(Users.username == username).first()
    @classmethod
    def user_login(cls, username: str):
        return Users.select(Users,Grade).where(Users.username == username).where(Users.is_del == 0).join(Grade,attr='grade').first()

    #获取所有用户id
    @classmethod
    def get_all_user_id(cls):
        return cls.undelete().select(cls.id).where(cls.is_del == 0).dicts()


    @classmethod
    def get_user_list(cls,keyword:str='',page: int = 1, page_size: int = 20):
        db = cls.undelete().select(cls.id, cls.username,cls.nickname,cls.status, cls.grade_id,cls.expirationTime,cls.createTime,Grade.grade_name).join(Grade,attr='grade').where(Users.is_del == 0)
        if keyword != "":
            db = db.where(cls.username.contains(keyword))

        user_list, paginate = paginator(db, page, page_size, "id desc")

        return user_list, paginate
