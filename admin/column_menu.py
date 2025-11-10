# -*- coding: UTF-8 -*-
'''
@Date    ：2025/6/24 11:42
@Describe
'''
from dotenv import load_dotenv
from fastapi import APIRouter
from pydantic import BaseModel

from common.function import success, fail
from models.get_columns_menu import get_columns_menu, add_column_menu, edit_column_menu, column_menu_delete, column_menu_is_show

router = APIRouter()
load_dotenv()


class AddColumnsMenu(BaseModel):
    menu_column_name: str
    parent_id: int
    action: str
    icon: str
    path: str
    navft: int
    is_all: int

class EidtColumnsMenu(BaseModel):
    id: int
    menu_column_name: str
    parent_id: int
    action: str
    icon: str
    navft: int
    path: str
    is_all: int



@router.get("/GetColumnsMenulList", summary="获取栏目菜单列表")
async def get_columns_menu_list():
    try:
        formatted_data = get_columns_menu()
        # return success(formatted_data)
        return success(
            {
                "data": list(formatted_data),
                "total": len(list(formatted_data)),
                "current_page": 1,
                "per_page": 100
            }
        )
    except Exception as e:
        return fail("获取失败")

@router.post("/addColumnMenu", summary="添加栏目菜单")
async def create_column_menu(item: AddColumnsMenu):
    try:
        add_column_menu(item.dict())
        return success("添加成功")
    except Exception as e:
        return fail("添加失败")

@router.post("/editColumnMenu", summary="编辑栏目菜单")
async def update_column_menu(item: EidtColumnsMenu):
    try:
        edit_column_menu(item.dict())
        return success("编辑成功")
    except Exception as e:
        return fail("编辑失败")


@router.get("/deleteColumnMenu", summary="删除栏目菜单")
async def delete_column_menu(id: int):
    try:
        column_menu_delete(id)
        return success("删除成功")
    except Exception as e:
        return fail("删除失败")

@router.get("/changeColumnMenuShowStatus", summary="设置栏目菜单是否显示")
async def update_column_menu_show_status(id: int, navft: int):
    try:
        column_menu_is_show(id, navft)
        return success("设置成功")
    except Exception as e:
        return fail("设置失败")