import datetime
import os
import shutil, uuid
from typing import List
from pydantic import BaseModel
from fastapi import Form, APIRouter, Depends, UploadFile, File
from dotenv import load_dotenv

from common.function import success, fail
from PIL import Image


from models.admin import Admin
from common import admin
from models.files import Files


router = APIRouter()
load_dotenv()


class Item(BaseModel):
    id: int


#上传文件
@router.post("/File")
def upload_file(file: UploadFile = File(...)):
    try:
        name, *suffix = file.filename.rsplit('.', 1)
        suffix = f'.{suffix[0]}' if suffix else ''

        # 判断文件类型
        if suffix not in ['.txt', '.md', '.xlsl', '.pdf', '.docx', '.csv', '.png', '.jpg', '.ico', '.svg']:
            return fail("文件类型不支持，支持txt,md,xlsl,pdf,docx,csv,png,jpg,ico,svg格式")
        # 判断文件大小
        if file.file.__sizeof__() > 1024 * 1024 * 10:
            return fail("文件大小不能超过50M")

        # 生成一个随机的UUID
        random_filename = str(uuid.uuid4())
        # 拼接文件名
        filename = f'{random_filename}'
        # 获取当前日期
        today = datetime.date.today()
        # 构建文件夹路径
        folder_path = f'media/models/{today.year}{today.month}{today.day}'
        original_path = f'{folder_path}/{filename}{suffix}'
        if not os.path.exists(folder_path):
            # 创建文件夹
            os.makedirs(folder_path, exist_ok=True)
        with open(original_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.close()
        return success({"filename":file.filename,"path":f'/{original_path}',"type":file.content_type,"suffix":suffix,"file_id": random_filename})
    except Exception as e:
        return fail(str(e))


#多文件上传
@router.post("/MultipleFile")
def MultipleFile(files: List[UploadFile] = File(...)):
    try:
        file_list = []
        for file in files:
            name, *suffix = file.filename.rsplit('.', 1)
            suffix = f'.{suffix[0]}' if suffix else ''

            # 判断文件类型
            if suffix not in ['.txt', '.md', '.xlsl', '.pdf', '.docx', '.csv']:
                return fail("文件类型不支持，支持txt,md,xlsl,pdf,docx,csv格式")
            # 判断文件大小
            if file.file.__sizeof__() > 1024 * 1024 * 50:
                return fail("文件大小不能超过50M")

            # 生成一个随机的UUID
            random_filename = str(uuid.uuid4())
            # 拼接文件名
            filename = f'{random_filename}'
            # 获取当前日期
            today = datetime.date.today()
            # 构建文件夹路径
            folder_path = f'media/models/{today.year}{today.month}{today.day}'
            original_path = f'{folder_path}/{filename}{suffix}'
            if not os.path.exists(folder_path):
                # 创建文件夹
                os.makedirs(folder_path, exist_ok=True)
            with open(original_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file.file.close()
            file_list.append({"filename": file.filename, "path": f'/{original_path}', "type": file.content_type,
                              "suffix": suffix, "file_id": random_filename})

        return success(file_list)
    except Exception as e:
        return fail(str(e))


#删除文件
@router.post("/DeleteFile")
def delete_file(item: Item):
    try:
        Files.del_file(item.id)
        return success("删除成功")
    except Exception as e:
        return fail(str(e))


#获取文件列表
@router.get("/GetFileList")
def get_file_list(current_admin: Admin = Depends(admin.get_current_user)):
    try:
        file_list = Files.get_user_file_list(current_admin.id)
        return success(list(file_list))
    except Exception as e:
        return fail(str(e))


def convert_jpeg_to_jpg(image_path):
    image = Image.open(image_path)
    image.save(image_path.replace(".jpeg", ".jpg"), "JPEG")
