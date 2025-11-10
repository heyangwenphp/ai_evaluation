import json
import random
from typing import List

from common.session import BaseModel, paginator
from peewee import CharField, IntegerField, ForeignKeyField, fn


class MenuColumns(BaseModel):
    class Meta:
        table_name = 'lv_columns'

    id = IntegerField()
    menu_column_name = CharField()  # 栏目菜单名称
    parent_id = IntegerField()  # 父级id
    grade_id = IntegerField() # 等级id
    controller = CharField() # 控制器
    action = CharField() # 英文菜单/操作方法
    icon = CharField() # 字体图标
    navft = IntegerField() # 是否在显示 1显示 0不显示·
    path = CharField() # 菜单路由
    sort = IntegerField() # 排序值，值越大越靠前
    is_all = IntegerField(default=0)  # 是否绑定智灵所有用户 1-是，0-否
    is_del = IntegerField(default=0)  # 是否删除 1-是，0-否



