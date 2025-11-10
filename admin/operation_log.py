from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from common import admin
from common.function import fail, success
from models.admin import Admin
from models.operation_log import OperationLog

router = APIRouter()

class Item(BaseModel):
    id: List[int]


#删除管理员操作日志
@router.post("/DeleteOperationLog", summary="删除管理员操作日志", name="删除管理员操作日志")
def DeleteOperationLog(item: Item, current_admin: Admin = Depends(admin.get_current_user)):
    try:
        OperationLog.delete_log(item.id)
        OperationLog.create_log(admin_id=current_admin.id, module="menu", content="删除管理员操作日志")
        return success("删除成功")
    except Exception as e:
        return fail(str(e))

#获取管理员操作日志列表
@router.get("/GetOperationLogList", summary="获取管理员操作日志列表", name="获取管理员操作日志列表")
def GetOperationLogList(content:str='',page: int = 1, size: int = 20):
    try:
        app_list, paginate = OperationLog.fetch_all(content,page, size)
        print(app_list)
        return success({"data": (app_list), "total": paginate['count'], "current_page": paginate['current_page'],
                        "per_page": size})
    except Exception as e:
        return fail(str(e))



