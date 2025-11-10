# python
import json
import tldextract
from fastapi import FastAPI, Request
from jose import jwt
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from core.config import settings
from index import user, files, columns, big_models, question
from models.users import Users as User
from utils.logger import logger

# 使用 JSONResponse 作为默认响应类，减少自动序列化分支触发
app = FastAPI(default_response_class=JSONResponse)

def safe_json_response(data, status_code=200):
    """
    将任意对象尽量转换为简单的 JSON 可序列化结构，
    遇到复杂/循环引用时使用 str() 作为后备。
    返回一个 Starlette JSONResponse。
    """
    try:
        body = json.loads(json.dumps(data, default=str))
    except Exception:
        body = {"data": str(data)}
    return JSONResponse(status_code=status_code, content=body)

# 如果确实需要 fastapi 的 jsonable_encoder，延迟导入以避免顶层循环导入
def _jsonable_encoder(obj, **kwargs):
    from fastapi.encoders import jsonable_encoder as _je  # 延迟导入
    return _je(obj, **kwargs)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["OPTIONS", "POST", "GET"],
    allow_headers=["*"],
)

@app.middleware("http")
async def check_token(request: Request, call_next):
    path = {'/Index/Login', '/Index/Register','/Index/GetBigModelsList','/'}

    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme

    if not host:
        return safe_json_response({"code": 301, "msg": "error", "data": "非法请求，拒绝服务"}, status_code=400)

    if ":" in host:
        host = host.split(":")[0]

    extracted = tldextract.extract(host)

    request.state.subdomain = extracted.subdomain
    request.state.domain = extracted.domain
    request.state.suffix = extracted.suffix
    request.state.full_domain = ".".join([p for p in [extracted.subdomain, extracted.domain, extracted.suffix] if p])
    request.state.scheme = scheme
    print(f"请求域名: {request.state.full_domain}, 协议: {request.state.scheme}")

    if request.url.path in path:
        response = await call_next(request)
        return response

    token = request.headers.get("token")
    if not token:
        return safe_json_response({"code": 301, "msg": "error", "data": "您的登录状态已过期，请重新登录"}, status_code=200)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user = User.single_by_id(uid=payload.get("sub"))
        if not user or user.status == 0:
            return safe_json_response({"code": 301, "msg": "error", "data": "您的登录状态已过期，请重新登录"}, status_code=200)
    except Exception as e:
        logger.error(f"Token 验证失败: {e}")
        return safe_json_response({"code": 301, "msg": "error", "data": "您的登录状态已过期，请重新登录"}, status_code=200)

    response = await call_next(request)
    return response

app.include_router(user.router, prefix="/Index")
app.include_router(big_models.router, prefix="/Index")
app.include_router(question.router, prefix="/Index")
app.include_router(files.router, prefix="/Index")
app.include_router(columns.router, prefix="/Index")

if __name__ == "__main__":
    import uvicorn

    # uvicorn ai_index:app --reload --port 8127 --workers 20 --host 0.0.0.0

    # uvicorn ai_index:app --reload --port 8131 --host 0.0.0.0
    # uvicorn ai_index:app --reload --port 8000 --host 0.0.0.0
    # uvicorn ai_index:app --reload --port 8127 --host 0.0.0.0
    # uvicorn ai_index:app --reload --port 8129 --host 0.0.0.0
    # kill -9 `ps -ef|grep ai_index:app|awk '{print $2}'`
    uvicorn.run("ai_index:app", host="0.0.0.0", port=8127, reload=False, workers=20)

# 如果问题仍然存在，建议在虚拟环境中重装/锁定兼容版本，例如（在 shell 中运行）:
# python -m pip uninstall -y fastapi starlette
# python -m pip install --upgrade "fastapi>=0.101.0" "pydantic==2.12.3" "starlette>=0.28.0"
# 然后重启服务。