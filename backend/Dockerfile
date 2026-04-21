FROM python:3.11-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令 - 使用 start_railway.py 以支持 Railway 的 PORT 环境变量
CMD ["python", "start_railway.py"]
