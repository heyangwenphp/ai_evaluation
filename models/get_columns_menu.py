# -*- coding: UTF-8 -*-
'''
@Author  ：pcy
@Date    ：2025/6/19 17:06 
@Describe
'''
import datetime

from peewee import JOIN

from models.enterprise.enterprise import MenuColumns, EnterpriseUserMenuSettings, EnterpriseMenuSettings
from models.grade import Grade
from models.users import Users


def build_menu_tree(menu_data, parent_id=0):
    tree = []
    for item in menu_data:
        if item['parent_id'] == parent_id:
            children = build_menu_tree(menu_data, item['id'])
            if children:
                item['children'] = children
            tree.append(item)
    return tree


def format_title(title, level, is_last=False):
    prefix = "├─" if not is_last else "└─"
    return prefix * (level) + title

    return prefix * (level) + action


def get_grade_name(grade_id):
    """
    获取会员名
    parm: grade_id: 会员id
    """
    grade = Grade.select().where(Grade.id == grade_id).first()
    if grade:
        return grade.grade_name
    else:
        return ""


def format_data(data, level=1):
    result = []
    for i, item in enumerate(data):
        is_last = (i == len(data) - 1)
        formatted_item = {
            "id": item["id"],
            "menu_column_name": item["menu_column_name"],
            "menu_column_level": format_title(item["menu_column_name"], level, is_last),
            "parent_id": item["parent_id"],
            "grade_id": item["grade_id"],
            "vip_grade": get_grade_name(item["grade_id"]),
            "controller": item["controller"],
            "action": item["action"],
            "icon": item["icon"],
            "navft": item["navft"],
            "path": item["path"],
            "is_all": item["is_all"],
            "is_delete": item["is_delete"],
            "createTime": item["createTime"],
            "updateTime": item["updateTime"],
            "is_delete": item["is_delete"]
        }
        result.append(formatted_item)
        if "children" in item:
            result.extend(format_data(item["children"], level + 1))
    return result


def get_columns_menu():
    columns_menu_list = MenuColumns.select().where(MenuColumns.is_delete == 0).dicts()
    tree = build_menu_tree(list(columns_menu_list))
    # print(tree)
    # 转换后的数据
    formatted_data = format_data(tree)
    # print(formatted_data)
    return formatted_data


def add_column_menu(columns_menu):
    """
    添加栏目菜单
    parm: columns_menu: 栏目菜单信息
    """
    if int(columns_menu["parent_id"]) == 0:
        columns_menu["controller"] = columns_menu["action"]
    else:
        parent_column_menu = MenuColumns.select().where(MenuColumns.id == columns_menu["parent_id"]).dicts().get()
        columns_menu["controller"] = parent_column_menu["controller"]

    mc = MenuColumns.create(**columns_menu)
    if columns_menu["is_all"] == 1:
        binding_to_zhiling(mc.id)
    elif columns_menu["is_all"] == 0:
        unbind_to_zhiling(mc.id)

def get_controller(parent_id):
    """
    获取最上级栏目菜单
    parm: parent_id: 栏目菜单父级id
    """
    parent_column_menu = MenuColumns.select().where(MenuColumns.id == parent_id).dicts().get()
    if parent_column_menu["parent_id"] == 0:
        return parent_column_menu["controller"]

    else:
        return get_controller(parent_column_menu["parent_id"])

def update_child(columns_menu):
    """
    更新子级栏目菜单
    parm: columns_menu: 栏目菜单信息
    """
    father_controller = columns_menu["action"]


    def update_child_column_menu(column_menu_id):
        child_menu = MenuColumns.select().where(MenuColumns.parent_id == column_menu_id)
        if child_menu.count() > 0:
            for child in child_menu:
                id = child.id
                MenuColumns.update(**{"controller":father_controller}).where(MenuColumns.id == id).execute()
                update_child_column_menu(child.id)

    update_child_column_menu(columns_menu["id"])
def edit_column_menu(columns_menu):
    """
    编辑栏目菜单
    parm: columns_menu: 栏目菜单信息
    """
    columns_menu["controller"] = columns_menu["action"]
    if int(columns_menu["parent_id"]) != 0:
        father_controller = get_controller(columns_menu["parent_id"])
        columns_menu["controller"] = father_controller
    else:
        update_child(columns_menu)
    old_info = MenuColumns.select().where(MenuColumns.id == columns_menu["id"]).dicts().get()
    old_is_all = old_info["is_all"]
    new_is_all = columns_menu["is_all"]
    MenuColumns.update(**columns_menu).where(MenuColumns.id == columns_menu["id"]).execute()
    if old_is_all != new_is_all:
        if columns_menu["is_all"] == 1:
            binding_to_zhiling(columns_menu["id"])
        elif columns_menu["is_all"] == 0:
            unbind_to_zhiling(columns_menu["id"])


def column_menu_delete(column_menu_id):
    """
    编辑栏目菜单
    parm: column_menu_id: 删除的栏目菜单id
    """
    MenuColumns.update(**{"is_delete": 1}).where(MenuColumns.id == column_menu_id).execute()

    # 同时删除所有使用到该栏目菜单的地方
    EnterpriseUserMenuSettings.update(
        **{"is_delete": 1}
    ).where(EnterpriseUserMenuSettings.menu_id == column_menu_id).execute()
    EnterpriseMenuSettings.update(
        **{"is_delete": 1}
    ).where(EnterpriseMenuSettings.menu_id == column_menu_id).execute()



def column_menu_is_show(column_menu_id, is_show):
    """
    设置栏目菜单是否显示
    parm: column_menu_id: 栏目菜单id
    parm: is_show: 显示状态：1-是，0-否
    """
    MenuColumns.update(**{"navft": is_show}).where(MenuColumns.id == column_menu_id).execute()

def unbind_to_zhiling(menu_id):
    """
    取消绑定智灵所有用户
    parm: menu_id: 栏目菜单id
    """
    menu_id_list = [menu_id]

    def get_child_menu(column_menu_id):
        child_menu = MenuColumns.select().where(MenuColumns.parent_id == column_menu_id)
        if not child_menu:
            return
        for child in child_menu:
            if child.id not in menu_id_list:
                menu_id_list.append(child.id)
            get_child_menu(child.id)

    # get_child_menu(menu_id)

    EnterpriseMenuSettings.update(**{"is_delete": 1}).\
        where(EnterpriseMenuSettings.enterprise_id == 1).\
        where(EnterpriseMenuSettings.menu_id.in_(menu_id_list)).execute()

    EnterpriseUserMenuSettings.update(**{"is_delete": 1}).\
        where(EnterpriseUserMenuSettings.enterprise_id == 1).\
        where(EnterpriseUserMenuSettings.menu_id.in_(menu_id_list)).execute()



    MenuColumns.update(**{"is_all": 0}).where(MenuColumns.id.in_(menu_id_list)).execute()


def binding_to_zhiling(menu_id):
    """
    绑定到智灵所有用户
    parm: menu_id: 栏目菜单id
    """
    menu_id_list = [menu_id]

    def get_child_menu(id):
        child_menu = MenuColumns.select().where(MenuColumns.parent_id == id)
        if not child_menu:
            return
        for child in child_menu:
            if child.id not in menu_id_list:
                menu_id_list.append(child.id)
            get_child_menu(child.id)

    # get_child_menu(menu_id)

    # 绑定栏目菜单给智灵企业
    enterprise_menu = EnterpriseMenuSettings.select().\
        where(EnterpriseMenuSettings.enterprise_id ==1).\
        where(EnterpriseMenuSettings.menu_id.in_(menu_id_list)).first()
    if enterprise_menu:
        EnterpriseMenuSettings.update(
            **{"is_delete": 0}
        ).where(EnterpriseMenuSettings.enterprise_id == 1).\
            where(EnterpriseMenuSettings.menu_id.in_(menu_id_list)).execute()
    else:
        EnterpriseMenuSettings.create(
            **{"enterprise_id": 1, "menu_id": menu_id_list[0]})

    # 获取所有绑定过或已绑定的智灵用户，全部更新状态为绑定
    zhiling_users_binded_menu_info = Users.select(Users.id.alias("user_id"), EnterpriseUserMenuSettings.menu_id.alias("menu_id")). \
        join(EnterpriseUserMenuSettings, JOIN.RIGHT_OUTER, on=(EnterpriseUserMenuSettings.user_id == Users.id)). \
        where(EnterpriseUserMenuSettings.menu_id.in_(menu_id_list)).\
        where(EnterpriseUserMenuSettings.enterprise_id == 1).\
        where(Users.is_del == 0)
    is_binded_user = [item.user_id for item in zhiling_users_binded_menu_info]

    EnterpriseUserMenuSettings.update(
        **{"is_delete": 0}
    ).where(EnterpriseUserMenuSettings.enterprise_id == 1).\
        where(EnterpriseUserMenuSettings.user_id.in_(is_binded_user)).\
        where(EnterpriseUserMenuSettings.menu_id.in_(menu_id_list)).execute()


    # 给没有绑定的用户新建
    zhiling_users = Users.select().where(Users.enterprise_id == 1).where(Users.is_del == 0)
    not_bindd_user = [user.id for user in zhiling_users if user.id not in is_binded_user]
    new_bind_user_menu = []
    for mc_id in menu_id_list:
        for user_id in not_bindd_user:
            new_bind_user_menu.append({
                "user_id": user_id,
                "enterprise_id": 1,
                "menu_id": mc_id,
                "createTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "updateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })

    EnterpriseUserMenuSettings.bulk_create([EnterpriseUserMenuSettings(**data) for data in new_bind_user_menu])

    MenuColumns.update(**{"is_all": 1}).where(MenuColumns.id.in_(menu_id_list)).execute()

