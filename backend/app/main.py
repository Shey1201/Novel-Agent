from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import novel_routes, generate_chapter, world_routes, agent_routes, asset_routes, skills, system_settings_api
from app.api import writers_room_api, stream_api, collaboration_api, cache_api, analysis_api, analytics_api, advanced_features_api, agent_room_api, download_api

app = FastAPI(title="Novel Agent Studio v3")

# 允许前端访问（本地和 Vercel）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
    ],
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
