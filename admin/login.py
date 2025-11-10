
from datetime import timedelta

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.requests import Request

from core import security
from core.config import settings
from models.admin import Admin
from common.function import fail, success
from models.admin_log import AdminLog

router = APIRouter()


class Item(BaseModel):
    username: str
    password: str


# 登录
@router.post("/login", summary="用户登录认证", name="登录")
def login(item: Item,request: Request):
    try:
        item.password = item.password.strip()
        item.username = item.username.strip()
        user = Admin.single_by_username(username=item.username)
        if user.is_del == 1:
            return fail("账号不存在")
        if not user:
            return fail("账号或密码错误")
        if not security.verify_password(item.password, user.password):
            return fail("账号或密码错误")
        if user.state == 0:
            return fail("账号已被禁用")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = security.create_access_token(user.id, expires_delta=access_token_expires)
        info = {
            "id": user.id,
            "username": user.username,
            "access_token": token,
            "role_id": user.role_id_id,
            "role_name": user.role_id.role_name,
        }

        ip = request.client.host

        AdminLog.create_log(admin_id=user.id, ip=ip)

        return success(info)
    except Exception as e:
        return fail("登录失败")





