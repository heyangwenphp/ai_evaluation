from typing import  Optional, List

from fastapi import APIRouter, Depends
from playhouse.shortcuts import model_to_dict
from pydantic import BaseModel

from common import admin
from core import security
from models.admin import Admin
from common.function import fail, success
from models.admin_log import AdminLog
from models.operation_log import OperationLog

router = APIRouter()





class Item(BaseModel):
    id: List[int]


#删除管理员登录日志
@router.post("/DeleteAdminLog", summary="删除管理员登录日志", name="删除管理员登录日志")
def DeleteAdminLog(item: Item, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        AdminLog.delete_log(item.id)
        OperationLog.create_log(admin_id=current_admin.id, module="admin_log", content="删除管理员登录日志")
        return success("删除成功")
    except Exception as e:
        return fail(str(e))

#获取管理员登录日志列表
@router.get("/GetAdminLogList", summary="获取管理员登录日志列表", name="获取管理员登录日志列表")
def GetAdminLogList(page: int = 1, size: int = 20):
    try:
        app_list, paginate = AdminLog.fetch_all(page, size)
        return success({"data": (app_list), "total": paginate['count'], "current_page": paginate['current_page'],
                        "per_page": size})
    except Exception as e:
        return fail(str(e))



