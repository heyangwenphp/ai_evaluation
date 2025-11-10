from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, ForeignKeyField,fn


class Style(BaseModel):
    """
    短片风格表
    """
    id = IntegerField()
    video_type = CharField()
    style_name = CharField()
    title = CharField()
    cueword = CharField()
    image = CharField()
    sort = IntegerField()
    is_del = IntegerField()



    class Meta:
        table_name = 'lv_style'

    @classmethod
    def create_style(cls, video_type:str, style_name: str, image:str):
        return cls.create(video_type=video_type,style_name=style_name, image=image,is_del=0)


    #更新风格
    @classmethod
    def update_style(cls, id: int,  image:str):
        return cls.update(image=image).where(cls.id == id).execute()



    @classmethod
    def single_by_id(cls, id: int):
        db = cls.undelete().select().where(cls.id == id)
        return db.first()

    @classmethod
    def single_by_style_name(cls, style_name: str):
        return cls.select().where(cls.style_name == style_name).first()

    @classmethod
    def single_by_style_video(cls, style_name: str,video_type: str):
        return cls.select(cls.id,cls.title).where(cls.style_name == style_name).where(cls.video_type == video_type).first()



    @classmethod
    def single_by_id_style_name(cls, id: int, style_name: str):
        db = cls.select().where(cls.id != id).where(cls.style_name == style_name)
        return db.first()

    #删除角色
    @classmethod
    def delete_style(cls, id: List[int]):
        return cls.update(is_del=1).where(cls.id.in_(id)).execute()


    #获取所有记录
    @classmethod
    def all_style_list(cls,video_type: str):
        return cls.undelete().select().where(cls.video_type == video_type).where(cls.is_del == 0).order_by(cls.sort.asc()).dicts()

    @classmethod
    def single_by_video_type(cls,is_pro: int):
        if is_pro == 1:
            return cls.select().where(cls.video_type != "创意短片").where(cls.is_del == 0).order_by(fn.Rand()).limit(1).get()
        else:
            return cls.select().where(cls.is_del == 0).order_by(fn.Rand()).limit(1).get()




    @classmethod
    def fetch_all(cls, page: int = 1, page_size: int = 10):
        db = cls.undelete().select().where(cls.is_del == 0)

        style_list, paginate = paginator(db, page, page_size, "id asc")

        return style_list, paginate