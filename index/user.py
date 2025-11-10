import datetime
from datetime import timedelta
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from common import deps
from models.users import Users
from common.function import fail, success, is_expire, error
from core import security
from core.config import settings
from utils.logger import logger

load_dotenv()

router = APIRouter()


class Item(BaseModel):
    username: str
    password: str
    confirm_password: Optional[str] = None
    expirationTime: Optional[str] = None



# pip3 install bcrypt==4.0.1
# 登录
@router.post("/Login", summary="用户登录认证", name="登录")
def login(item: Item):
    try:
        item.password = item.password.strip()
        item.username = item.username.strip()
        if item.username == "" or item.password == "":
            return fail("账号或密码不能为空")
        user = Users.user_login(username=item.username)
        logger.info(f"用户登录信息：{user}")
        if not user:
            return fail("账号或密码错误")

        if not security.verify_password(item.password, user.password):
            return fail("账号或密码错误")

        if user.status == 0:
            return fail("账号已被禁用")

        # 判断账号是否到期
        delta = is_expire(user)
        user = Users.single_by_id(user.id)
        if delta < 0:
            return fail("账号已到期")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = security.create_access_token(user.id, expires_delta=access_token_expires)
        info = {
            "id": user.id,
            "name": user.username,
            "expirationTime": user.expirationTime,
            "delta": delta,
            "grade_id": user.grade_id.id,
            "grade_name": user.grade_id.grade_name,
            "token": token,
        }
        return success(info)
    except Exception as e:
        return fail(str(e))

#注册
@router.post("/Register", summary="用户注册", name="注册")
def register(item: Item):
    try:
        item.password = item.password.strip()
        item.username = item.username.strip()
        if item.username == "" or item.password == "":
            return fail("账号或密码不能为空")
        if item.password != item.confirm_password:
            return fail("两次输入的密码不一致")

        #判断用户是否已经存在
        existing_user = Users.single_by_username(item.username)
        if existing_user:
            return fail("用户已存在")
        expirationTime = str(datetime.date.today() + datetime.timedelta(days=29)) + " 23:59:59"
        user = Users.create_user(
            username=item.username,
            nickname=item.username,
            expirationTime=expirationTime,
            password=security.get_password_hash(item.password),
        )
        logger.info(f"用户注册信息：{user}")
        if not user:
            return fail("注册失败")

        return success("注册成功")
    except Exception as e:
        return fail(str(e))




# 获取用户信息
@router.get("/GetUserInfo", summary="获取用户信息", name="获取用户信息")
def GetUserInfo(user: Users = Depends(deps.get_current_user)):
    try:
        if user:
            # 判断账号是否到期
            delta = is_expire(user)
            user = Users.single_by_id(user.id)

            if user.status == 0 and user.enterprise_id != 1:
                #return fail("账号已被禁用")
                return error(301, "账号已被禁用")

            info = {
                "id": user.id,
                "name": user.username,
                "expirationTime": user.expirationTime,
                "grade_id": user.grade_id.id,
                "grade_name": user.grade_id.grade_name,
                "delta": delta,
            }
            return success(info)
        else:
            return fail("用户不存在")
    except Exception as e:
        return fail(str(e))







