"""
Railway 等云平台启动脚本：从环境变量 PORT 读取端口并启动 uvicorn。
平台会注入 PORT，若未设置则默认 8000（本地开发）。
"""
import os
import uvicorn

if __name__ == "__main__":
    # 读取 Railway 提供的 PORT 环境变量
    port = int(os.environ.get("PORT", "8000"))
    
    print(f"[Railway] Starting uvicorn on 0.0.0.0:{port}", flush=True)
    
    # 使用 0.0.0.0 监听所有接口
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
