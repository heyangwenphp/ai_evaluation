from typing import List

from common.session import BaseModel
from peewee import CharField, IntegerField

from models.role import Role


class Menu(BaseModel):
    """
    分类表
    """
    id = IntegerField(primary_key=True, sequence=True)
    pid = IntegerField()
    mid = IntegerField()
    title = CharField()
    controller = CharField()
    action = CharField()
    icon = CharField()
    path = CharField()
    navft = IntegerField()
    sort = IntegerField()
    is_del = IntegerField()

    class Meta:
        table_name = 'lv_menu'

    @classmethod
    def create_menu(cls, pid: int, title: str, action: str, icon: str, navft: int, sort: int):
        if pid == 0:
            mid = 1
            controller = action.capitalize()
        else:
            res = Menu.get_mid(pid=pid)
            # if res['pid'] == 0:
            #     mid = 1
            # else:
            #     mid = 2
            mid = res['mid'] + 1
            controller = res['controller']

        path = '/admin/' + action
        return Menu.create(pid=pid, title=title, controller=controller, action=action, icon=icon, path=path,
                           navft=navft, mid=mid, sort=sort, is_del=0)

    @classmethod
    def update_menu(cls, id: int, pid: int, title: str, action: str, icon: str, navft: int, sort: int):
        if pid == 0:
            mid = 1
            controller = action.capitalize()
        else:
            res = Menu.get_mid(pid=pid)
            # if res['pid'] == 0:
            #     mid = 1
            # else:
            #     mid = 2
            mid = res['mid'] + 1
            controller = res['controller']

        path = '/admin/' + action
        return Menu.update(pid=pid, title=title, controller=controller, action=action, icon=icon, path=path,
                           navft=navft, sort=sort, mid=mid, is_del=0).where(Menu.id == id).execute()

    @classmethod
    def delete_menu(cls, id: int):
        return Menu.update(is_del=1).where(Menu.id == id).execute()

    @classmethod
    def update_state(cls, id: int,navft: int):
        return Menu.update(navft=navft).where(Menu.id == id).execute()

    @classmethod
    def get_list(cls, title=""):
        if title == "":
            return Menu.select().where(Menu.is_del == 0).order_by(Menu.mid.asc()).order_by(Menu.sort.desc()).dicts()
        else:
            return Menu.select().where(Menu.title.contains(title)).where(Menu.is_del == 0).order_by(Menu.mid.asc()).order_by(Menu.sort.desc()).dicts()

    @classmethod
    def get_menu_list(cls,role_id:int):
        #获取角色权限
        route_id = Role.single_by_id(role_id)
        if not route_id.route_id:
            return []
        if route_id.is_del == 1:
            return []
        route_id_list = route_id.route_id.split(',')
        return Menu.select().where(Menu.is_del == 0).where(Menu.navft == 1).where(Menu.id.in_(route_id_list)).order_by(Menu.mid.asc()).order_by(Menu.sort.desc()).dicts()

    @classmethod
    def get_menu_id_list(cls,route_id:List[str]):
        return Menu.select().where(Menu.is_del == 0).where(Menu.mid < 3).where(Menu.id.in_(route_id)).order_by(Menu.mid.asc()).order_by(Menu.sort.desc()).dicts()

    @classmethod
    def get_last_list(cls):
        res = Menu.select().where(Menu.mid == 2).where(Menu.is_del == 0).order_by(Menu.sort.desc()).dicts()
        if res is None:
            res = Menu.select().where(Menu.mid == 1).where(Menu.is_del == 0).order_by(Menu.sort.desc()).dicts()
        return res

    # 获取mid
    @classmethod
    def get_mid(cls, pid: int):
        return Menu.select().where(Menu.id == pid).dicts().first()

    # 获取title是否存在
    @classmethod
    def get_title(cls, title: str):
        return Menu.select(Menu.title).where(Menu.title == title).first()

    @classmethod
    def get_menu_info(cls, id: int):
        return Menu.select().where(Menu.id == id).dicts().first()

    # 判断是否为父级
    @classmethod
    def is_parent(cls, id: int):
        menu = Menu.select(Menu.mid).where(Menu.id == id).where(Menu.is_del == 0).dicts().first()
        if menu is None:
            return True
        else:
            if menu['mid'] == 0:
                return True
            else:
                return False

        # 判断用户项目是否存在

    @classmethod
    def is_menu_exist(cls, project_id: int, id: int):
        menu = Menu.select(Menu.mid).where(Menu.id == id).where(Menu.is_del == 0).dicts().first()
        if menu is None:
            return False
        else:
            return True

    @classmethod
    def is_menu_title_exist(cls, project_id: int, title: str):
        menu = Menu.select().where(Menu.title == title).where(Menu.is_del == 0).first()
        if menu is None:
            return False
        else:
            return menu

