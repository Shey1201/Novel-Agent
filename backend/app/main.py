import os
from pathlib import Path

# 加载 .env 文件（如果在本地开发环境）
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded environment from {env_path}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import novel_routes, generate_chapter, world_routes, agent_routes, asset_routes, skills, system_settings_api, novel_management, agent_management
from app.api import writers_room_api, stream_api, collaboration_api, cache_api, analysis_api, analytics_api, advanced_features_api, agent_room_api, download_api

app = FastAPI(title="Novel Agent Studio v3")

# 允许前端访问（本地、Vercel 和 Railway）
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://novel-agent-eta.vercel.app",
]

# 从环境变量读取额外的 CORS 域名
additional_origins = os.getenv("CORS_ORIGINS", "")
if additional_origins:
    origins.extend([o.strip() for o in additional_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(novel_routes.router)
app.include_router(generate_chapter.router)
app.include_router(world_routes.router)
app.include_router(agent_routes.router)
app.include_router(asset_routes.router)
app.include_router(skills.router)
app.include_router(system_settings_api.router)
app.include_router(novel_management.router)
app.include_router(agent_management.router)

# v3 新功能
app.include_router(writers_room_api.router)
app.include_router(stream_api.router)
app.include_router(collaboration_api.router)
app.include_router(cache_api.router)
app.include_router(analysis_api.router)
app.include_router(analytics_api.router)
app.include_router(advanced_features_api.router)
app.include_router(agent_room_api.router)
app.include_router(download_api.router)
