import datetime
from datetime import timedelta
from typing import Any, Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from common import  admin
from core import security
from core.config import settings
from models.admin import Admin
from models.menu import Menu
from models.operation_log import OperationLog
from models.role import Role
from models.role_button import RoleButton
from common.function import fail, success

router = APIRouter()


class Item(BaseModel):
    id: Optional[int] = ''
    role_name: str
    describe: Optional[str] = ''
    route_id: Optional[str] = ''


class DeleteItem(BaseModel):
    id: List[int]


class RouteItem(BaseModel):
    id: int
    route_id: str


# 添加
@router.post("/CreateRole", summary="角色添加", name="添加")
def CreateRole(item: Item, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        role = Role.single_by_role_name(role_name=item.role_name)
        if role:
            return fail("该角色已存在")
        Role.create_role(
            role_name=item.role_name,
            describe=item.describe,
        )
        OperationLog.create_log(admin_id=current_admin.id, module="role", content="添加角色")
        return success("添加成功")
    except Exception as e:
        return fail(str(e))


# 修改角色
@router.post("/UpdateRole", summary="修改角色", name="修改角色")
def UpdateRole(item: Item, current_admin: Admin = Depends(admin.get_current_user)):
    try:

        role = Role.single_by_id_role_name(id=item.id, role_name=item.role_name)
        if role:
            return fail("角色已存在")

        Role.update_role_info(
            id=item.id,
            role_name=item.role_name,
            describe=item.describe,
        )
        OperationLog.create_log(admin_id=current_admin.id, module="role", content="修改角色")
        return success("修改成功")
    except Exception as e:
        return fail(str(e))


# 删除角色
@router.post("/DeleteRole", summary="删除角色", name="删除角色")
def DeleteRole(item: DeleteItem, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        Role.delete_role(item.id)
        OperationLog.create_log(admin_id=current_admin.id, module="role", content="删除角色")
        return success("删除成功")
    except Exception as e:
        return fail(str(e))


# 获取角色列表
@router.get("/GetRoleList", summary="获取角色列表", name="获取角色列表")
def GetRoleList(page: int = 1, size: int = 20):
    try:
        app_list, paginate = Role.fetch_all(page, size)
        return success({"data": (app_list), "total": paginate['count'], "current_page": paginate['current_page'],
                        "per_page": size})
    except Exception as e:
        return fail(str(e))


# 获取所有角色列表
@router.get("/GetRoleAllList", summary="获取所有角色列表", name="获取所有角色列表")
def GetRoleAllList():
    try:
        app_list = Role.all_list()
        return success(list(app_list))
    except Exception as e:
        return fail(str(e))


# 更新角色权限
@router.post("/UpdateRoleRoute", summary="更新角色权限", name="更新角色权限")
def UpdateRoleRoute(item: RouteItem, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        menu_id_list = item.route_id.split(',')
        menu_list = Menu.get_menu_id_list(item.route_id.split(','))
        role_button = {}
        for menu in menu_list:
            role_button['role_id'] = item.id
            role_button['menus_id'] = menu['id']
            role_button['action'] = menu['action']
            role_button['title'] = menu['title']
            role_button['add'] = 0
            role_button['edit'] = 0
            role_button['delete'] = 0
            role_button['status'] = 0
            role_button['export'] = 0
            # role_button['import'] = 0
            role_button['view'] = 0
            role_button['role'] = 0
            role_button['shipment'] = 0
            role_button['batchAdd'] = 0
            role_button['batchDelete'] = 0
            role_button['reset'] = 0
            butt = Menu.select().where(Menu.pid == menu['id']).where(Menu.mid == 3).dicts()
            if butt:
                for but in butt:
                    if str(but["id"]) in menu_id_list:
                        if but["action"] == "batchdelete":
                            role_button['batchDelete'] = 1
                        else:
                            role_button[but["action"]] = 1
                    # if but['action'] == 'add':
                    #     role_button['add'] = 1
                    # if but['action'] == 'edit':
                    #     role_button['edit'] = 1
                    # if but['action'] == 'delete':
                    #     role_button['delete'] = 1
                    # if but['action'] == 'status':
                    #     role_button['status'] = 1
                    # if but['action'] == 'export':
                    #     role_button['export'] = 1
                    # if but['action'] == 'import':
                    #     role_button['import'] = 1
                    # if but['action'] == 'view':
                    #     role_button['view'] = 1
                    # if but['action'] == 'role':
                    #     role_button['role'] = 1
                    # if but['action'] == 'shipment':
                    #     role_button['shipment'] = 1
                    # if but['action'] == 'batchadd':
                    #     role_button['batchAdd'] = 1
                    # if but['action'] == 'batchdelete':
                    #     role_button['batchDelete'] = 1
                    # if but['action'] == 'reset':
                    #     role_button['reset'] = 1
                    if role_button:
                        button_permission = RoleButton.select().where(RoleButton.menus_id == role_button['menus_id']). \
                            where(RoleButton.role_id == item.id).\
                            first()

                        if button_permission:
                            RoleButton.update(**role_button). \
                                where(RoleButton.menus_id == role_button['menus_id']). \
                                where(RoleButton.role_id == item.id). \
                                where(RoleButton.is_del == 0). \
                                execute()
                        else:
                            RoleButton.create_role(role_button)

        Role.update_role_route(item.id, item.route_id)
        OperationLog.create_log(admin_id=current_admin.id, module="role", content="更新角色权限")
        return success("修改成功")
    except Exception as e:
        return fail(str(e))


