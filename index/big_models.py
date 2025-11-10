from dotenv import load_dotenv
from fastapi import APIRouter
from common.function import fail, success
from models.big_models import BigModels
from utils.logger import logger

load_dotenv()

router = APIRouter()

# 获取大模型列表
@router.get("/GetBigModelsList", summary="获取大模型列表", name="获取大模型列表")
def GetBigModelsList():
    try:
        model_list = BigModels.get_models_list()
        return success(list(model_list))
    except Exception as e:
        logger.error(f"获取大模型列表异常：{e}")
        return fail(str(e))















