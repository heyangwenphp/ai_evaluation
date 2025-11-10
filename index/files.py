import shutil,uuid
import os
import datetime
from fastapi import Form, APIRouter, Depends, UploadFile, File
from dotenv import load_dotenv
from common import deps
from common.function import success, fail
from models.files import Files
from models.users import Users
from utils.handle_execl import HandleExecl
from utils.logger import logger
from pydantic import BaseModel
router = APIRouter()
load_dotenv()
class DelItem(BaseModel):
    id: int

#上传文件
@router.post("/UploadFiles")
def UploadFiles(file:UploadFile = File(...),user: Users = Depends(deps.get_current_user)):
    try:
        name, *suffix = file.filename.rsplit('.', 1)
        suffix = f'.{suffix[0]}' if suffix else ''
        # 判断文件类型
        if suffix not in ['.xls','.xlsx']:
            return fail("文件类型不支持，支持xls、xlsx格式")
        # 判断文件大小
        # 获取文件实际大小
        file.file.seek(0, 2)  # 移动到文件末尾
        size = file.file.tell()
        file.file.seek(0)  # 回到文件开头
        if size > 1024 * 1024 * 10:
            return fail("文件大小不能超过10M")
        # 生成一个随机的UUID
        random_filename = str(uuid.uuid4())
        # 拼接文件名
        filename = f'{random_filename}'
        # 获取当前日期
        today = datetime.date.today()
        # 构建文件夹路径
        folder_path = f'media/xlsx/{today.year}{today.month}{today.day}'
        original_path = f'{folder_path}/{filename}{suffix}'
        if not os.path.exists(folder_path):
            # 创建文件夹
            os.makedirs(folder_path, exist_ok=True)
        with open(original_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.close()
        # 2、 读取execl表格内容,获得df
        df = HandleExecl().read_excel(original_path)
        # # 获得维度列表
        # dimension_list = HandleExecl().get_dimension_list(df)

        # 3、 检查表格必填列是否存在. is_required_columns是Ture执行下面内容，如果为False，打印错误信息
        is_required_columns, e = HandleExecl().check_required_columns(df)
        if not is_required_columns:
            e_str = ",".join(e)
            return fail(f"输入表格缺少必填列: {e_str}")
        questions_list = HandleExecl().get_questions_list(df)
        if not questions_list or len(questions_list) == 0:
            return fail("表格中未检测到有效题目，请检查表格内容")
        if len(questions_list) > 500:
            return fail("表格中题目数量不能超过500，请精简后重新上传")
        files=Files.create_files(user_id=user.id, file_name=file.filename, path=f'/{original_path}',suffix=suffix)
        return success({"filename":file.filename,"path":f'/{original_path}',"type":file.content_type,"suffix":suffix,"file_id": files.id})
    except Exception as e:
        return fail(str(e))




