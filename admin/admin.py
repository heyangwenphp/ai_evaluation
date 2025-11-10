from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from common import admin
from core import security
from models.admin import Admin
from common.function import fail, success
from models.operation_log import OperationLog

router = APIRouter()

class CurrentUserSetPassword(BaseModel):
    user_id: Optional[int]
    user_name: Optional[str]
    original_password: Optional[str]
    new_password: Optional[str]
    confirm_password: Optional[str]



class Item(BaseModel):
    id: Optional[int] = ''
    username: Optional[str] = ''
    password: Optional[str] = ''
    confirm_password: Optional[str] = ''
    state: Optional[int] = 1
    role_id: Optional[int] = 1


class DeleteItem(BaseModel):
    id: Optional[int]


# 添加
@router.post("/CreateAdmin", summary="用户添加", name="添加")
def CreateAdmin(item: Item, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        item.password = item.password.strip()
        item.confirm_password = item.confirm_password.strip()
        item.username = item.username.strip()
        if item.password != item.confirm_password:
            return fail("两次密码不一致")
        user = Admin.single_by_username(username=item.username)
        if user:
            return fail("该用户已存在")

        Admin.create_admin(
            username=item.username,
            password=security.get_password_hash(item.password),
            role_id=item.role_id,
            state=item.state,
        )

        OperationLog.create_log(admin_id=current_admin.id, module="enterprise", content="添加管理员")
        return success("添加成功")
    except Exception as e:
        return fail(str(e))


@router.post("/UpdateCurrentUserPassword", summary="修改当前登录用户的密码")
def UpdateCurrentUserPassword(item: CurrentUserSetPassword, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        current_user = Admin.select().where(Admin.id == item.user_id).where(Admin.username == item.user_name).first()
        if not security.verify_password(item.original_password, current_user.password):
            return fail("原密码错误")
        if item.original_password == item.new_password:
            return fail("新密码不能与原密码一致")
        if item.new_password != item.confirm_password:
                return fail("新密码跟确认密码不一致")

        Admin.update(
            password=security.get_password_hash(item.new_password)
        ).where(Admin.id == item.user_id).where(Admin.username == item.user_name).execute()
        return success("密码修改成功")
    except Exception as e:
        return fail("修改密码失败")

# 修改管理员
@router.post("/UpdateAdmin", summary="修改管理员", name="修改管理员")
def UpdateAdmin(item: Item, current_admin: Admin = Depends(admin.get_current_user)):
    try:

        item.username = item.username.strip()
        if item.password != '' and item.confirm_password != '':
            item.password = item.password.strip()
            item.confirm_password = item.confirm_password.strip()
            if item.password != item.confirm_password:
                return fail("两次密码不一致")
            password = security.get_password_hash(item.password)
        else:
            password = ''

        user = Admin.single_by_id_username(id=item.id, username=item.username)
        if user:
            return fail("用户已存在")

        Admin.update_admin(
            id=item.id,
            username=item.username,
            password=password,
            role_id=item.role_id,
            state=item.state,
        )
        OperationLog.create_log(admin_id=current_admin.id, module="enterprise", content="修改管理员")
        return success("修改成功")
    except Exception as e:
        return fail(str(e))


# 修改管理员状态
@router.post("/UpdateAdminState", summary="修改管理员状态", name="修改管理员状态")
def UpdateAdminState(item: Item, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        Admin.update_state(
            id=item.id,
            state=item.state,
        )
        OperationLog.create_log(admin_id=current_admin.id, module="enterprise", content="修改管理员状态")
        return success("修改成功")
    except Exception as e:
        return fail(str(e))


# 删除管理员
@router.post("/DeleteAdmin", summary="删除管理员", name="删除管理员")
def DeleteAdmin(item: DeleteItem, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        Admin.delete_user(item.id)
        OperationLog.create_log(admin_id=current_admin.id, module="enterprise", content="删除管理员")
        return success("删除成功")
    except Exception as e:
        return fail(str(e))


# 获取管理员列表
@router.get("/GetAdminList", summary="获取管理员列表", name="获取管理员列表")
def GetAdminList(page: int = 1, size: int = 20):
    try:
        app_list, paginate = Admin.fetch_all(page, size)
        for index, item in enumerate(app_list):
            if item["role_is_del"] == 1:
                app_list[index]["role_name"] = ""
                app_list[index]["role_id"] = ""
        return success({
            "data": (app_list),
            "total": paginate['count'],
            "current_page": paginate['current_page'],
            "per_page": size
        })
    except Exception as e:
        return fail(str(e))

@router.get("/GetUserRole", summary="获取用户角色", name="获取用户角色")
def get_user_role(user_id: int):
    try:
        user = Admin.single_by_id(uid=user_id)
        info = {
            "id": user_id,
            "username": user.username,
            "role_id": user.role_id_id,
            "role_name": user.role_id.role_name,
        }
        return success(info)
    except Exception as e:
        return fail("获取失败")

@router.get("/GetCurrentUserInfo", summary="获取用户")
def get_user_status(user_id: int):
    try:
        user = Admin.select().where(Admin.id == user_id).first()
        info = {
            "id": user_id,
            "username": user.username,
            "state": user.state,
            "is_del": user.is_del,
            "role_id": user.role_id_id,
            "role_is_del": user.role_id.is_del,
        }
        return success(info)
    except Exception as e:
        return fail("获取失败")
