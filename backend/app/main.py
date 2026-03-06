from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import novel_routes, generate_chapter, world_routes, agent_routes, asset_routes, skills

app = FastAPI(title="Multi-Agent Novel Backend")

# 允许本地 Next.js 前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
