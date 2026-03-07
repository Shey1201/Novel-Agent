# 向量数据库配置指南

## 概述

Novel Agent Studio v3 使用三层记忆系统：
- **L1 Short Memory**: 内存中的 StoryMemory
- **L2 Semantic Memory**: 向量数据库 (Qdrant/Weaviate)
- **L3 Knowledge Graph**: 图数据库 (Neo4j)

本文档介绍如何配置 L2 和 L3 存储。

## 方案一：Qdrant (推荐)

### 1. 安装 Qdrant

**Docker 方式（推荐）:**

```bash
# 拉取镜像
docker pull qdrant/qdrant

# 运行容器
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

**Python 客户端安装:**

```bash
pip install qdrant-client
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# Qdrant 配置
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-api-key  # 如果启用了认证
```

### 3. 验证连接

```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
print(client.get_collections())
```

## 方案二：Weaviate

### 1. 安装 Weaviate

**Docker Compose:**

```yaml
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:1.24.0
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: ''
      CLUSTER_HOSTNAME: 'node1'
```

### 2. 配置环境变量

```env
# Weaviate 配置
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-api-key
```

### 3. 修改代码

在 `backend/app/memory/vector_store.py` 中切换实现：

```python
# 从 Qdrant 切换到 Weaviate
from weaviate import Client as WeaviateClient

class WeaviateVectorStore:
    def __init__(self, url: str, api_key: Optional[str] = None):
        self.client = WeaviateClient(url, auth_client_secret=api_key)
```

## 方案三：Neo4j 知识图谱

### 1. 安装 Neo4j

**Docker 方式:**

```bash
# 拉取镜像
docker pull neo4j:5.15.0-community

# 运行容器
docker run -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -v $(pwd)/neo4j_data:/data \
  neo4j:5.15.0-community
```

### 2. 配置环境变量

```env
# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### 3. 访问 Neo4j Browser

打开 http://localhost:7474 使用浏览器界面管理图谱。

## 内存模式（开发/测试）

如果不需要持久化存储，可以使用内存模式：

```python
# Vector Store 内存模式
vector_store = InMemoryVectorStore()

# Knowledge Graph 内存模式  
knowledge_graph = InMemoryKnowledgeGraph()
```

系统会自动检测环境变量，如果没有配置则使用内存模式。

## 生产环境建议

### Qdrant 集群部署

```yaml
# docker-compose.yml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__CLUSTER__ENABLED=true
      - QDRANT__CLUSTER__P2P__PORT=6335
    volumes:
      - ./qdrant_storage:/qdrant/storage
    deploy:
      replicas: 3
```

### Neo4j 集群部署

参考 Neo4j 官方文档配置因果集群（Causal Clustering）。

## 性能优化

### Qdrant 优化

1. **索引配置**: 使用 HNSW 索引加速相似度搜索
2. **分片策略**: 按 novel_id 分片存储
3. **内存限制**: 配置 `QDRANT__STORAGE__MEMORY_LIMIT`

### Neo4j 优化

1. **索引**: 为常用查询字段创建索引
2. **约束**: 使用唯一约束确保数据一致性
3. **查询优化**: 使用 EXPLAIN 分析查询性能

## 监控

### Qdrant 监控

```bash
# 查看集群状态
curl http://localhost:6333/cluster

# 查看集合信息
curl http://localhost:6333/collections
```

### Neo4j 监控

```cypher
// 查看数据库状态
CALL dbms.listQueries()

// 查看索引使用情况
CALL db.indexes()
```

## 故障排除

### Qdrant 连接失败

1. 检查服务是否运行: `docker ps | grep qdrant`
2. 检查端口是否被占用: `netstat -an | grep 6333`
3. 查看日志: `docker logs <container_id>`

### Neo4j 连接失败

1. 检查认证信息是否正确
2. 检查防火墙设置
3. 查看日志: `docker logs <container_id>`

## 迁移指南

### 从内存模式迁移到 Qdrant

```python
# 1. 导出内存数据
memories = memory_store.get_all()

# 2. 导入到 Qdrant
vector_store = QdrantVectorStore(url="http://localhost:6333")
for memory in memories:
    vector_store.add_memory(memory)
```

### 备份与恢复

**Qdrant:**
```bash
# 备份
docker cp qdrant:/qdrant/storage ./backup

# 恢复
docker cp ./backup qdrant:/qdrant/storage
```

**Neo4j:**
```bash
# 备份
docker exec neo4j neo4j-admin backup --from=localhost --backup-dir=/backups

# 恢复
docker exec neo4j neo4j-admin restore --from=/backups --database=neo4j --force
```
