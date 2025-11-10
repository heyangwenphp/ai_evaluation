import json, time, os, datetime
import logging
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.encoders import jsonable_encoder
from jose import jwt, JWTError
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from admin import file, admin, login, role, admin_log, menu, operation_log


from core.config import settings
from models.admin import Admin

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# 允许的前端域名，生产环境应该限制为具体域名
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "https://yuanjingtest.zeelin.cn",
    "https://yuanjing.zeelin.cn"
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    # 限制跨域源为具体域名，提高安全性
    allow_origins=ALLOWED_ORIGINS,
    # 跨域请求是否支持 cookie，默认是 False，如果为 True，allow_origins 必须为具体的源，不可以是 ["*"]
    allow_credentials=True,
    # 允许跨域请求的 HTTP 方法列表，默认是 ["GET"]
    allow_methods=["OPTIONS", "POST", "GET", "PUT", "DELETE"],
    # 允许跨域请求的 HTTP 请求头列表，默认是 []，可以使用 ["*"] 表示允许所有的请求头
    # 当然 Accept、Accept-Language、Content-Language 以及 Content-Type 总之被允许的
    allow_headers=["*"],
    # 可以被浏览器访问的响应头, 默认是 []，一般很少指定
    # expose_headers=["*"]
    # 设定浏览器缓存 CORS 响应的最长时间，单位是秒。默认为 600，一般也很少指定
    # max_age=1000
)
# 简单的用户缓存，避免每次请求都查询数据库
user_cache = {}
CACHE_EXPIRE_TIME = 300  # 5分钟缓存过期

def get_cached_user(user_id: str) -> Optional[Admin]:
    """获取缓存的用户信息"""
    if user_id in user_cache:
        user_data, timestamp = user_cache[user_id]
        if time.time() - timestamp < CACHE_EXPIRE_TIME:
            return user_data
        else:
            # 缓存过期，删除
            del user_cache[user_id]
    return None

def cache_user(user_id: str, user_data: Admin):
    """缓存用户信息"""
    user_cache[user_id] = (user_data, time.time())

# 路由中间件
@app.middleware("http")
async def check_token(request: Request, call_next):
    # 白名单路径，不需要token验证
    whitelist_paths = ['/Api/login', '/']

    # 记录请求日志
    logger.info(f"Request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")

    # 获取可信 host
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")

    if not host:
        logger.warning("Request missing Host header")
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({
                "code": 400,
                "msg": "error",
                "data": "请求错误"
            })
        )

    if ":" in host:
        # 去除端口
        host = host.split(":")[0]



    # 白名单路径直接放行
    if request.url.path in whitelist_paths:
        response = await call_next(request)
        return response

    # 获取token
    token = request.headers.get("token")
    if not token:
        logger.warning("Request missing token")
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder({
                "code": 301,
                "msg": "error",
                "data": "token不能为空"
            })
        )

    try:
        # 解码JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")

        if not user_id:
            logger.warning("Token missing user ID")
            return JSONResponse(
                status_code=200,
                content=jsonable_encoder({
                    "code": 301,
                    "msg": "error",
                    "data": "token格式错误"
                })
            )

        # 先尝试从缓存获取用户
        user = get_cached_user(user_id)
        if not user:
            # 缓存中没有，从数据库查询
            user = Admin.single_by_id(uid=int(user_id))
            if user:
                cache_user(user_id, user)

        if not user:
            logger.warning(f"User not found for ID: {user_id}")
            return JSONResponse(
                status_code=200,
                content=jsonable_encoder({
                    "code": 301,
                    "msg": "error",
                    "data": "用户验证失败"
                })
            )

        # 检查用户状态
        if user.state != 1:
            logger.warning(f"User {user_id} is disabled")
            return JSONResponse(
                status_code=200,
                content=jsonable_encoder({
                    "code": 301,
                    "msg": "error",
                    "data": "用户已被禁用"
                })
            )

    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder({
                "code": 301,
                "msg": "error",
                "data": "token已失效"
            })
        )
    except ValueError as e:
        logger.warning(f"Invalid user ID in token: {str(e)}")
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder({
                "code": 301,
                "msg": "error",
                "data": "token格式错误"
            })
        )
    except Exception as e:
        logger.error(f"Unexpected error in token validation: {str(e)}")
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder({
                "code": 301,
                "msg": "error",
                "data": "服务器内部错误"
            })
        )

    response = await call_next(request)
    return response


# 上传文件
app.include_router(file.router, prefix="/Api")
app.include_router(admin.router, prefix="/Api")
app.include_router(admin_log.router, prefix="/Api")
app.include_router(operation_log.router, prefix="/Api")
app.include_router(role.router, prefix="/Api")
app.include_router(login.router, prefix="/Api")
app.include_router(menu.router, prefix="/Api")




if __name__ == "__main__":
    # uvicorn ai_admin:app --reload --port 8126 --workers 20 --host 0.0.0.0
    # uvicorn ai_admin:app --reload --port 8126 --host 0.0.0.0
    # kill -9 `ps -ef|grep ai_admin:app|awk '{print $2}'`

    # netstat -antp |grep 8081
    import uvicorn

    uvicorn.run("ai_admin:app", host="0.0.0.0", port=8130, reload=False, workers=1)
    # uvicorn.run("ai_admin:app", host="127.0.0.1", port=8126, reload=False, workers=20)
