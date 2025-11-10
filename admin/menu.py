# Desc: 菜单相关接口
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from common import admin
from common.function import success, fail
from models.admin import Admin
from models.menu import Menu
from models.operation_log import OperationLog
from models.role import Role
from models.role_button import RoleButton

router = APIRouter()
load_dotenv()


class CreateItem(BaseModel):
    pid: int = 0
    title: str
    action: Optional[str] = ''
    icon: Optional[str] = ''
    path: Optional[str] = ''
    navft: Optional[int] = 1
    sort: Optional[int] = 0


class UpdateItem(BaseModel):
    id: int
    pid: int = 0
    title: str
    action: Optional[str] = ''
    icon: Optional[str] = ''
    path: Optional[str] = ''
    navft: Optional[int] = 1
    sort: Optional[int] = 0


class DeleteItem(BaseModel):
    id: int


class StateItem(BaseModel):
    id: int
    navft: int


# 创建菜单
@router.post("/CreateMenu")
async def CreateMenu(item: CreateItem, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        Menu.create_menu(item.pid, item.title, item.action, item.icon, item.navft, item.sort)
        OperationLog.create_log(admin_id=current_admin.id, module="menu", content="添加菜单")
        return success('添加成功')
    except Exception as e:
        return fail(str(e))


# 修改菜单
@router.post("/UpdateMenu")
async def UpdateMenu(item: UpdateItem, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        if item.id is None or item.id == '':
            return fail('id不能为空')
        Menu.update_menu(item.id, item.pid, item.title, item.action, item.icon, item.navft, item.sort)
        OperationLog.create_log(admin_id=current_admin.id, module="menu", content="修改菜单")
        return success('修改成功')
    except Exception as e:
        return fail(str(e))


# 修改状态
@router.post("/UpdateMenuState")
async def UpdateMenuState(item: StateItem, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        if item.id is None or item.id == '':
            return fail('id不能为空')
        Menu.update_state(item.id, item.navft)
        OperationLog.create_log(admin_id=current_admin.id, module="menu", content="修改菜单状态")
        return success('修改成功')
    except Exception as e:
        return fail(str(e))


# 删除菜单
@router.post("/DeleteMenu")
async def DeleteMenu(item: DeleteItem, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        if item.id is None or item.id == '':
            return fail('id不能为空')
        Menu.delete_menu(item.id)
        OperationLog.create_log(admin_id=current_admin.id, module="menu", content="删除菜单")
        return success('删除成功')
    except Exception as e:
        return fail(str(e))


# 获取菜单管理列表
@router.get("/GetMenuList")
async def GetMenuList(title: str = ''):
    try:
        menu_list = Menu.get_list(title)
        # tree = build_menu_tree(list(menu_list))
        tree = transform_to_tree(list(menu_list))
        # 转换后的数据
        formatted_data = format_data(tree)
        # return success(
        #     {
        #         "data": formatted_data,
        #         "total": len(list(menu_list)),
        #         "current_page": 1,
        #         "per_page": 200
        #     }
        # )
        return success(tree)
    except Exception as e:
        return fail(str(e))


# 获取左侧角色菜单列表
@router.get("/GetMenus")
async def GetMenus(current_admin: Admin = Depends(admin.get_current_user)):
    try:

        menu_list = Menu.get_menu_list(current_admin.role_id)
        tree = build_menu_tree(list(menu_list))
        return success(tree)
    except Exception as e:
        return fail(str(e))


# 获取操作按钮权限
@router.get("/GetButtons")
async def GetButtons(current_admin: Admin = Depends(admin.get_current_user)):
    try:
        button_list = RoleButton.single_by_role_id(current_admin.role_id)
        button = {}

        use = {'add': True, 'batchAdd': True, 'export': True, 'batchDelete': True, 'status': True, 'state': True,
               'view': True, 'edit': True, 'delete': True, 'role': True, 'shipment': True}
        if button_list:
            for key in button_list:
                active = {}
                active['add'] = True if key['add'] == 1 else False
                active['batchAdd'] = True if key['batchAdd'] == 1 else False
                active['export'] = True if key['export'] == 1 else False
                active['batchDelete'] = True if key['batchDelete'] == 1 else False
                active['status'] = True if key['status'] == 1 else False
                active['view'] = True if key['view'] == 1 else False
                active['edit'] = True if key['edit'] == 1 else False
                active['delete'] = True if key['delete'] == 1 else False
                active['role'] = True if key['role'] == 1 else False
                active['reset'] = True if key['reset'] == 1 else False
                active['shipment'] = True if key['shipment'] == 1 else False
                button[key['action']] = active

        button['useHooks'] = use
        button['useComponent'] = use

        return success(button)
    except Exception as e:
        return fail(str(e))


# 获取最后节点菜单列表
@router.get("/getMenuListLast")
async def getMenuListLast():
    try:
        menu_list = Menu.get_list()
        tree = build_menu_tree(list(menu_list))
        result = extract_leaf_nodes(tree)
        return success(result)
    except Exception as e:
        return fail(str(e))


# 权限管理全部菜单
@router.get("/GetMenuAllList")
async def GetMenuAllList():
    try:
        menu_list = Menu.get_list(title='')
        tree = build_menu_tree(list(menu_list))
        return success(tree)
    except Exception as e:
        return fail(str(e))

@router.get("/GetAllMenu")
async def all_menu():
    try:
        menu_list = Menu.get_list('')
        return success(list(menu_list))
    except Exception as e:
        return fail(str(e))
# 获取角色菜单id
@router.get("/GetMenuRoleInList")
async def GetMenuRoleInList(id: int):
    try:
        route_info = Role.single_by_id(id)
        if not route_info:
            return success([])

        if not route_info.route_id:
            return success([])

        menu_list = route_info.route_id.split(',')
        role_menu_list = []
        for menu_id in menu_list:
            role_menu_list.append(int(menu_id))
        # for i in range(len(menu_list)):
        #     route_id[i] = int(route_id[i])
        return success(role_menu_list)
    except Exception as e:
        return fail(str(e))


def extract_leaf_nodes(data):
    result = []
    for item in data:
        if "children" in item and item["children"]:
            # 如果有子节点，递归调用函数处理子节点
            child_result = extract_leaf_nodes(item["children"])
            result.extend(child_result)
        else:
            # 如果没有子节点，将当前节点添加到结果中
            if item['pid'] != 0:
                result.append(item)
    return result


def transform_to_tree(datas):
    """
    数据格式整合成目录树
    datas：列表數據
    """
    node_dict = {}
    root_nodes = []

    # 遍历数据，创建节点字典
    for item in datas:
        node = {
            "id": item["id"],
            "createTime": item["createTime"],
            "updateTime": item["updateTime"],
            "pid": item["pid"],
            "mid": item["mid"],
            "title": item["title"],
            "controller": item["controller"],
            "action": item["action"],
            "icon": item["icon"],
            "path": item["path"],
            "navft": item["navft"],
            "sort": item["sort"],
            "is_del": item["is_del"],
            "father": "",
            'children': []
        }
        node_dict[item["id"]] = node

    # 遍历数据，构建树结构
    for item in datas:
        node = node_dict[item["id"]]
        parent_id = item["pid"]

        # 如果 parent_id 为 0，表示根节点
        if parent_id == 0:
            node["father"] = node["title"]
            root_nodes.append(node)
        else:
            # 否则，将当前节点添加到其父节点的 children 列表中
            if parent_id in node_dict:
                parent_node = node_dict[parent_id]
                node["father"] = parent_node["title"]
                parent_node['children'].append(node)
            else:
                # 如果父节点不存在，将其作为根节点处理
                root_nodes.append(node)

    return root_nodes

def build_menu_tree(menu_data, parent_id=0):
    tree = []
    for item in menu_data:
        if item['pid'] == parent_id:
            children = build_menu_tree(menu_data, item['id'])
            if children:
                item['children'] = children

            tree.append(item)

    return tree


# synthesis
def format_title(title, level, is_last=False):
    prefix = "├─" if not is_last else "└─"
    return prefix * (level) + title


def format_action(action, level, is_last=False):
    prefix = "├─" if not is_last else "└─"
    return prefix * (level) + action


def format_data(data, level=1):
    result = []
    for i, item in enumerate(data):
        is_last = (i == len(data) - 1)
        formatted_item = {
            "id": item["id"],
            "createTime": item["createTime"],
            "updateTime": item["updateTime"],
            "pid": item["pid"],
            "mid": item["mid"],
            "title": item["title"],
            "titles": format_title(item["title"], level, is_last),
            "controller": item["controller"],
            "action": item["action"],
            "actions": format_action(item["action"], level, is_last),
            "icon": item["icon"],
            "path": item["path"],
            "navft": item["navft"],
            "sort": item["sort"],
            "is_del": item["is_del"]
        }
        result.append(formatted_item)
        if "children" in item:
            result.extend(format_data(item["children"], level + 1))
    return result
