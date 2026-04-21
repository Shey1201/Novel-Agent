import os
from pathlib import Path

# 加载 .env 文件（如果在本地开发环境）
backend_root = Path(__file__).parent.parent
project_root = backend_root.parent
for env_path in (backend_root / ".env", project_root / ".env"):
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
        print(f"Loaded environment from {env_path}")
        break

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import novel_routes, generate_chapter, world_routes, agent_routes, asset_routes, skills, system_settings_api, novel_management, agent_management, category_management, messages_routes
from app.api import stream_api, cache_api, analysis_api, analytics_api, advanced_features_api, agent_room_api, download_api, memory_api
from app.core.logging_config import setup_logging

# 配置日志
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE", "logs/app.log")
setup_logging(log_level=log_level, log_file=log_file)


# 自定义 JSONResponse 以支持中文显示
class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        import json
        return json.dumps(content, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


app = FastAPI(
    title="Novel Agent Studio v3",
    description="AI驱动的小说创作平台API",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    default_response_class=CustomJSONResponse
)

# 允许前端访问（本地、Vercel 和 Railway）
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://novel-agent-eta.vercel.app",
    "https://novel-agent-ten.vercel.app",
]

# 从环境变量读取额外的 CORS 域名
additional_origins = os.getenv("CORS_ORIGINS", "")
if additional_origins:
    origins.extend([o.strip() for o in additional_origins.split(",") if o.strip()])

# 允许任意 *.vercel.app 预览/生产域名
allow_origin_regex = r"https://[a-z0-9-]+\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)



@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/debug/env")
async def debug_env():
    """调试端点：检查环境变量"""
    import os
    return {
        "supabase_url_set": bool(os.getenv("SUPABASE_URL")),
        "supabase_service_key_set": bool(os.getenv("SUPABASE_SERVICE_KEY")),
        "next_public_supabase_url_set": bool(os.getenv("NEXT_PUBLIC_SUPABASE_URL")),
        "next_public_supabase_anon_key_set": bool(os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")),
        "supabase_url_preview": os.getenv("SUPABASE_URL", "")[:30] + "..." if os.getenv("SUPABASE_URL") else "Not set",
    }


@app.get("/api/debug/errors")
async def debug_errors():
    """调试端点：获取错误统计"""
    from app.core.error_monitor import get_error_monitor
    monitor = get_error_monitor()
    errors = monitor.get_all_errors()
    return {
        "stats": monitor.get_error_stats(),
        "errors": [e.to_dict() for e in errors[:50]]  # 只返回最近50个
    }


@app.get("/api/debug/errors/{error_id}")
async def debug_error_detail(error_id: str):
    """调试端点：获取错误详情"""
    from app.core.error_monitor import get_error_monitor
    monitor = get_error_monitor()
    error = monitor.get_error(error_id)
    if error:
        return error.to_dict()
    return {"error": "Error not found"}, 404


@app.post("/api/debug/errors/{error_id}/resolve")
async def resolve_error(error_id: str):
    """调试端点：标记错误为已解决"""
    from app.core.error_monitor import get_error_monitor
    monitor = get_error_monitor()
    if monitor.resolve_error(error_id):
        return {"message": "Error resolved"}
    return {"error": "Error not found"}, 404


@app.delete("/api/debug/errors")
async def clear_errors():
    """调试端点：清除所有错误"""
    from app.core.error_monitor import get_error_monitor
    monitor = get_error_monitor()
    monitor.clear_errors()
    return {"message": "All errors cleared"}


# 保留旧路径的兼容性（将在未来版本移除）
@app.get("/health")
async def health_check_legacy():
    """兼容旧路径的健康检查"""
    return {"status": "ok", "note": "请使用 /api/health"}


@app.get("/debug/env")
async def debug_env_legacy():
    """兼容旧路径的调试端点"""
    import os
    return {
        "supabase_url_set": bool(os.getenv("SUPABASE_URL")),
        "supabase_service_key_set": bool(os.getenv("SUPABASE_SERVICE_KEY")),
        "next_public_supabase_url_set": bool(os.getenv("NEXT_PUBLIC_SUPABASE_URL")),
        "next_public_supabase_anon_key_set": bool(os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")),
        "supabase_url_preview": os.getenv("SUPABASE_URL", "")[:30] + "..." if os.getenv("SUPABASE_URL") else "Not set",
        "note": "请使用 /api/debug/env"
    }


app.include_router(novel_routes.router)
app.include_router(generate_chapter.router)
app.include_router(world_routes.router)
app.include_router(agent_routes.router)
app.include_router(asset_routes.router)
app.include_router(skills.router)
app.include_router(system_settings_api.router)
app.include_router(novel_management.router)
app.include_router(agent_management.router)
app.include_router(category_management.router)

# v3 新功能
app.include_router(stream_api.router)
app.include_router(cache_api.router)
app.include_router(analysis_api.router)
app.include_router(analytics_api.router)
app.include_router(advanced_features_api.router)
app.include_router(agent_room_api.router)
app.include_router(messages_routes.router)
app.include_router(download_api.router)
app.include_router(memory_api.router)


# ============ 全局异常处理 ============

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理 HTTP 异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP错误",
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求参数验证错误"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "参数验证错误",
            "detail": str(exc),
            "errors": exc.errors(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常"""
    import traceback
    import logging
    from app.core.error_monitor import get_error_monitor
    
    logger = logging.getLogger(__name__)
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    logger.error(f"请求路径: {request.url.path}")
    logger.error(f"请求方法: {request.method}")
    logger.error(f"异常类型: {type(exc).__name__}")
    
    # 记录到错误监控
    monitor = get_error_monitor()
    error_record = monitor.capture_exception(
        exc,
        context={
            "path": str(request.url.path),
            "method": request.method,
            "request_id": str(id(request)),
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "detail": str(exc),
            "type": type(exc).__name__,
            "path": str(request.url.path),
            "request_id": str(id(request)),
            "error_id": error_record.id
        }
    )
