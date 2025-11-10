import json
import os
import re
import time
import uuid
from collections import namedtuple

import cv2

import requests
from PIL import Image

from common.session import db
from models.users import Users
from utils.logger import logger
import datetime
import random
# pip3 install pycryptodome


# 常量定义
sKey = b"dde4b1f8a9e6b814"
ivParameter = b"dde4b1f8a9e6b814"
# 这个正则表达式匹配 emoji 表情
emoji_pattern = re.compile("[\U0001F600-\U0001F64F\u2600-\u26FF\u2700-\u27BF\u2B50\u231A\u231B\u3030\u2B06\u2194\u25AA\u2B1B\u2B50\u2B06\u2194\u25AA\u2B1B\u200D\u200C\u26A0\u26D4\u2702\u2705\u2B06\u1F3C6\u2600]")




def remove_emoji(text: str) -> str:
    return emoji_pattern.sub(r'', text)
def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    if fps == 0:
        return 0
    duration = frames / fps
    return duration  # 单位：秒

def convert_to_jpg(image_path):
    # 只处理 png、jpeg
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in ['.png', '.jpeg']:
        return image_path  # 不是目标格式，直接返回

    jpg_path = os.path.splitext(image_path)[0] + '.jpg'
    with Image.open(image_path) as img:
        rgb_img = img.convert('RGB')
        rgb_img.save(jpg_path, 'JPEG')
    #os.remove(image_path)  # 删除原文件
    return jpg_path

def generate_order_id():
    # 获取当前时间
    now = datetime.datetime.now()
    # 格式化时间
    time_str = now.strftime("%Y%m%d%H%M%S")
    # 生成6位随机数
    random_str = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    # 组合时间字符串和随机字符串
    order_id = time_str + random_str
    return order_id

def resize_and_crop(input_image_path, output_image_path, size):
    image = Image.open(input_image_path)
    image = image.resize(size)  # 改变图像大小
    image = image.crop((0, 0, size[0], size[1]))  # 裁剪图像
    image.save(output_image_path)

#裁剪图片
def crop_image_max(image_path,original_path):
    print("image_path")
    print(image_path)
    try:
        # 获取当前日期
        today = datetime.date.today()
        # 构建文件夹路径
        folder_path = f'media/{today.year}{today.month}{today.day}'
        if not os.path.exists(folder_path):
            # 创建文件夹
            os.makedirs(folder_path, exist_ok=True)
        r = requests.get(image_path, timeout=120)  # 第二种   import requests
        with open(original_path, 'wb') as f:
            print("下载图片")
            f.write(r.content)
        #host = os.getenv("HOST")
        original_path = original_path.replace(".","")
        original_path = f'/{original_path}'
        return original_path
    except Exception as e:
        print(str(e))
        logger.error(f"下载图片失败: {str(e)}")
        return ""

def download_image(image_path):
    print("image_path")
    print(image_path)
    time.sleep(1)
    try:
        # 获取当前日期
        today = datetime.date.today()
        # 构建文件夹路径
        folder_path = f'media/{today.year}{today.month}{today.day}'
        if not os.path.exists(folder_path):
            # 创建文件夹
            os.makedirs(folder_path, exist_ok=True)

        original_filename = str(uuid.uuid4())
        suffix = '.jpg'
        original_path = f'{folder_path}/{original_filename}{suffix}'
        r = requests.get(image_path, timeout=180)  # 第二种   import requests
        with open(original_path, 'wb') as f:
            print("下载图片")
            f.write(r.content)
        #host = os.getenv("HOST")
        original_path = f'/{original_path}'
        print(original_path)
        return original_path
    except Exception as e:
        print(str(e))
        logger.error(f"下载图片失败: {str(e)}")
        return ""

# # 加密
# def psw_encrypt(src):
#     key = sKey
#     iv = ivParameter
#     # 创建AES加密器
#     cipher = AES.new(key, AES.MODE_CBC, iv)
#     # 使用PKCS5Padding填充数据
#     padded_data = pad(src.encode(), AES.block_size)
#     # 加密数据
#     encrypted_data = cipher.encrypt(padded_data)
#     # 返回Base64编码结果
#     return base64.urlsafe_b64encode(encrypted_data).decode()
#
#
# # 解密
# def psw_decrypt(src):
#     key = sKey
#     iv = ivParameter
#     # 修复Base64字符串长度
#     src += '=' * (-len(src) % 4)
#     # Base64解码
#     encrypted_data = base64.urlsafe_b64decode(src)
#     # 创建AES解密器
#     cipher = AES.new(key, AES.MODE_CBC, iv)
#     # 解密数据并去除填充
#     decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
#     return decrypted_data.decode()


def getContent(content):
    content = content.replace('"', "")
    content = content.replace('**', "")
    content = content.replace("\\n\\n", "<br/>")
    content = content.replace("\\n", "<br/>")
    content = content.replace("\n\n", "<br/>")
    content = content.replace("\n", "<br/>")
    return content


def getbalance(key):
    try:
        url = "https://api.deepseek.com/user/balance"
        payload = {}
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + key
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)
        balance = json.loads(response.text)
        res = {'total_balance': balance['balance_infos'][0]['total_balance'],
               'granted_balance': balance['balance_infos'][0]['granted_balance'],
               'topped_up_balance': balance['balance_infos'][0]['topped_up_balance']}
        return res
    except Exception as e:
        print(e)
        return False

#判断会员是否过期
def is_expire(user):
    # 将字符串转换为日期
    expirationTime = datetime.datetime.strptime(user.expirationTime, "%Y-%m-%d %H:%M:%S").date()
    # 获取当前日期
    currentTime = datetime.date.today()
    # 计算两个日期之间的天数差值
    delta = (expirationTime - currentTime).days
    # 如果差值小于0，说明已经过期
    if delta < 0:
        # 手动管理事务
        db.begin()
        try:
                #清除次数，并记录日志
                #FrequencyLog.create_frequency_log(user.id, user.frequency, 1, "会员过期扣除")
                # frequency_updated_rows=Users.update_frequency_id(user.id,0)
                # integral_updated_rows=Users.update_integral_id(user.id,0)
                if int(user.integral) > 0 and user.enterprise_id ==1:


                    Users.update_grade_integral_frequency(user.id,1,0,0,0)



                # if frequency_updated_rows == 0 and integral_updated_rows == 0:
                #     print("No rows updated")
                #     # 抛出异常
                #     raise Exception("更新失败")
                logger.debug(f"会员到期：用户：{user.id}，到期时间：{expirationTime}")
                db.commit()
        except Exception as e:
            logger.error(f"会员验证：用户：{user.id}，是否过期验证失败")
            db.rollback()
            print(e)
    return delta


#点数扣除
def integral_deduction(user, integral, describe,genre):
    try:
        with db.atomic():  # 用上下文确保绑定在同一个事务里
            # 重新拉取用户数据
            user = Users.single_by_id(user.id)
            if float(user.integral) < float(integral):
                raise Exception("点数不足")

            remaining_integral = float(user.integral) - float(integral)

            # 日志记录和积分更新操作

            Users.update_integral_id(user.id, remaining_integral)

            logger.debug(f"扣除点数成功：用户：{user.id}，扣除数量：{integral}")
            return "True"
    except Exception as e:
        logger.error(f"扣除点数失败：用户：{user.id}，失败原因：{str(e)}，扣除数量：{integral}")
        #raise Exception("点数扣除失败")
        return str(e)

#点数增加
def integral_increase(user, integral, describe,genre):
    try:
        with db.atomic():  # 用上下文确保绑定在同一个事务里
            # 清除次数，并记录日志
            user = Users.single_by_id(user.id)
            remaining_integral = float(user.integral) + float(integral)

            Users.update_integral_id(user.id, remaining_integral)
            logger.debug(f"增加点数成功：用户：{user.id}，增加数量：{integral}")
    except Exception as e:
        logger.error(f"增加点数失败：用户：{user.id}，失败原因：{str(e)}，增加数量：{integral}")
        #raise Exception("点数增加失败")




def success(data):
    return {"code": 200, "message": "success", "data": data}


def fail(data):
    return {"code": 500, "message": "error", "data": data}


def error(code,data):
    return {"code": code, "message": "error", "data": data}


#按数字提取和排序
def extract_and_sort_by_number(input_str):
    # 定义一个命名元组来存储名称和数字
    Entry = namedtuple('Entry', ['name', 'number'])
    # 匹配名称和括号内的数字
    pattern = r'(\w+)\((\d+)\)'
    matches = re.findall(pattern, input_str)
    # 创建Entry对象的列表
    entries = [Entry(name, int(number)) for name, number in matches]
    # 根据数字从大到小、名称长度（长的在前）进行排序
    sorted_entries = sorted(entries, key=lambda x: (-x.number, -len(x.name)))
    # 格式化输出排序后的结果
    #sorted_str = ','.join(f"{entry.name}:{entry.number}" for entry in sorted_entries)
    sorted_str = ','.join(f"{entry.name}" for entry in sorted_entries)
    return sorted_str


#从括号中提取数字
def extract_numbers_from_parentheses(input_str):
    # 定义一个正则表达式模板，用于匹配括号前的文本和括号内的数字
    pattern = r'(\w+)\((\d+)\)'
    # 使用re.findall函数找到所有匹配项
    matches = re.findall(pattern, input_str)
    print(matches)
    # 遍历匹配项，并按指定格式构建输出字符串
    output = ','.join([f"{name}:{number}" for name, number in matches])
    return output


#判断字符串是否存在于列表中
def is_string_in_list(lst, s):
    return s in lst


#从列表中删除元素
def remove_element(arr, val):
    return [element for element in arr if element != val]


#判断字符串是否存在于列表中
def is_char_multiple_times(s, char):
    return s.count(char) > 1


#断数组是否同时包含多个元素
def contains_elements(arr, elements):
    return set(elements).issubset(set(arr))


#采集文本
def get_text(url):
    try:
        url = "https://r.jina.ai/" + url
        print(url)
        # 发送get请求
        response = requests.request("GET", url, headers={"x-respond-with": "text"})
        return response.text
    except Exception as e:
        print(e)
        return ""
