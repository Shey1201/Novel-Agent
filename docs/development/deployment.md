# 部署指南

本文档介绍 Novel Agent Studio 的生产环境部署方案。

## 目录

- [部署架构](#部署架构)
- [环境准备](#环境准备)
- [后端部署](#后端部署)
- [前端部署](#前端部署)
- [Docker部署](#docker部署)
- [监控与日志](#监控与日志)
- [备份策略](#备份策略)

## 部署架构

### 单机部署

```
┌─────────────────────────────────────┐
│           Nginx (反向代理)           │
│         端口: 80/443                │
├─────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐   │
│  │   前端      │  │   后端      │   │
│  │  Next.js    │  │  FastAPI    │   │
│  │   :3000     │  │   :8000     │   │
│  └─────────────┘  └─────────────┘   │
│                                     │
│  ┌─────────────────────────────┐    │
│  │      数据目录 (./data)       │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### 分离部署

```
┌─────────────┐         ┌─────────────┐
│   Nginx     │────────▶│   前端      │
│  (静态文件)  │         │  CDN/静态托管 │
└─────────────┘         └─────────────┘
       │
       ▼
┌─────────────┐         ┌─────────────┐
│   后端API   │────────▶│   数据存储   │
│   FastAPI   │         │  文件系统   │
└─────────────┘         └─────────────┘
```

## 环境准备

### 服务器要求

| 配置项 | 最低要求 | 推荐配置 |
|--------|----------|----------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 20GB | 50GB+ SSD |
| 带宽 | 5Mbps | 10Mbps+ |

### 系统环境

- **操作系统**: Ubuntu 22.04 LTS / CentOS 8 / Windows Server 2019+
- **Python**: 3.9+
- **Node.js**: 20+
- **Nginx**: 1.20+

### 环境变量

创建 `.env.production` 文件：

```env
# API配置
OPENAI_API_KEY=your_production_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# 后端配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_WORKERS=4

# 前端配置
NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# 数据目录
DATA_DIR=/var/data/novel-agent

# 日志级别
LOG_LEVEL=INFO
```

## 后端部署

### 1. 代码部署

```bash
# 创建应用目录
sudo mkdir -p /opt/novel-agent/backend
sudo chown -R $USER:$USER /opt/novel-agent

# 克隆代码
cd /opt/novel-agent
git clone <repository-url> .

# 创建虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 使用Gunicorn运行

```bash
# 安装gunicorn
pip install gunicorn

# 启动服务（4个worker）
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/novel-agent/access.log \
  --error-logfile /var/log/novel-agent/error.log \
  --daemon
```

### 3. 使用Systemd管理

创建服务文件 `/etc/systemd/system/novel-agent-backend.service`：

```ini
[Unit]
Description=Novel Agent Backend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/novel-agent/backend
Environment="PATH=/opt/novel-agent/backend/venv/bin"
Environment="OPENAI_API_KEY=your_api_key"
ExecStart=/opt/novel-agent/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable novel-agent-backend
sudo systemctl start novel-agent-backend
sudo systemctl status novel-agent-backend
```

## 前端部署

### 1. 构建生产版本

```bash
cd /opt/novel-agent/frontend
npm ci
npm run build
```

### 2. Nginx配置

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL证书配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 前端静态文件
    location / {
        root /opt/novel-agent/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

### 3. 启动Nginx

```bash
sudo nginx -t
sudo systemctl restart nginx
```

## Docker部署

### 1. 后端Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY app/ ./app/

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 前端Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

### 3. Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATA_DIR=/app/data
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

### 4. 启动Docker服务

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 监控与日志

### 日志配置

后端日志配置：

```python
# backend/app/core/logging.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                '/var/log/novel-agent/app.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
```

### 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 预期响应
{"status": "ok"}
```

### 监控指标

建议监控的关键指标：

- API响应时间
- 错误率
- LLM API调用次数和成本
- 磁盘使用率
- 内存使用率

## 备份策略

### 数据备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/novel-agent"
DATA_DIR="/opt/novel-agent/backend/data"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/data_$DATE.tar.gz $DATA_DIR

# 保留最近30天的备份
find $BACKUP_DIR -name "data_*.tar.gz" -mtime +30 -delete
```

### 定时备份

```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /opt/novel-agent/scripts/backup.sh
```

### 数据恢复

```bash
# 解压备份
tar -xzf data_20240101_020000.tar.gz -C /opt/novel-agent/backend/
```

## 安全建议

1. **API密钥管理**
   - 使用环境变量存储敏感信息
   - 定期轮换API密钥
   - 限制API密钥的权限范围

2. **网络安全**
   - 使用HTTPS
   - 配置防火墙规则
   - 限制不必要的端口暴露

3. **数据安全**
   - 定期备份
   - 加密敏感数据
   - 控制文件权限

## 故障排查

### 常见问题

1. **服务无法启动**
   - 检查日志文件
   - 验证环境变量
   - 检查端口占用

2. **API响应慢**
   - 检查LLM API状态
   - 监控服务器资源
   - 调整worker数量

3. **前端无法访问**
   - 检查Nginx配置
   - 验证后端服务状态
   - 检查防火墙设置

## 相关文档

- [开发环境搭建](setup-guide.md)
- [后端API参考](backend-api-reference.md)
