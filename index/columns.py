import datetime

from fastapi import APIRouter, Depends
from dotenv import load_dotenv
from common import deps
from common.function import success, fail
from models.columns import MenuColumns
from models.users import Users

router = APIRouter()
load_dotenv()


#用户获取菜单权限
@router.get("/GetUserMenu")
async def GetUserMenu(user: Users = Depends(deps.get_current_user)):
    try:

        #user_columns = EnterpriseUserSettings.query_enterprise_user_menu(enterprise_id=user.enterprise_id, user_id=user.id,menu_id=None)
        user_columns = []
        menu_id = [item.menu_id for item in user_columns]
        menu_info = MenuColumns.select().where(MenuColumns.id.in_(menu_id)).order_by(MenuColumns.sort.desc()).dicts()
        #menu_list = []
        ai_video = 0
        music_mv = 0
        explanation_video = 0
        for menu in menu_info:
            if "ai_video" in menu['action']:
                ai_video = 1
            if "music_mv" in menu['action']:
                music_mv = 1
            if "explanation_video" in menu['action']:
                explanation_video = 1

        menu_list = format_data(list(menu_info))
        menu_list = build_menu_tree(menu_list)


        return success({"menu_list": menu_list, "ai_video": ai_video, 'music_mv': music_mv,
                        "explanation_video": explanation_video})
    except Exception as e:
        return fail(str(e))


def build_menu_tree(menu_data, parent_id=0):
    tree = []
    for item in menu_data:
        if item['parent_id'] == parent_id:
            children = build_menu_tree(menu_data, item['id'])
            if children:
                item['children'] = children
            tree.append(item)
    return tree

def format_data(data):
    result = []
    for item in data:
        formatted_item = {
            "id": item["id"],
            "parent_id": item["parent_id"],
            "name": item["menu_column_name"],
            "path": item["path"],
            "isMenu": item["navft"],
            "icon": item["icon"],
        }
        result.append(formatted_item)
    return result