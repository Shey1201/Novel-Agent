"""
L3: World Memory - 知识图谱
使用 Neo4j 存储角色关系和世界设定
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

# 尝试导入 Neo4j
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Neo4j not available, using in-memory graph")


@dataclass
class Relationship:
    """关系"""
    source: str
    target: str
    relation_type: str
    properties: Dict[str, Any]


@dataclass
class Entity:
    """实体"""
    id: str
    name: str
    entity_type: str  # character/location/item/organization
    properties: Dict[str, Any]


class KnowledgeGraph:
    """
    知识图谱 - L3 世界记忆
    
    存储：
    - 角色关系
    - 地理位置
    - 物品归属
    - 组织关系
    """
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        
        if NEO4J_AVAILABLE:
            self._init_neo4j()
        else:
            self._init_memory()
    
    def _init_neo4j(self):
        """初始化 Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            self.storage_type = "neo4j"
        except Exception as e:
            print(f"Neo4j connection failed: {e}, falling back to memory")
            self._init_memory()
    
    def _init_memory(self):
        """初始化内存存储"""
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self.storage_type = "memory"
    
    def close(self):
        """关闭连接"""
        if self.storage_type == "neo4j" and hasattr(self, 'driver'):
            self.driver.close()
    
    # ==================== Entity Operations ====================
    
    def create_entity(
        self,
        novel_id: str,
        entity_id: str,
        name: str,
        entity_type: str,
        properties: Dict[str, Any] = None
    ) -> str:
        """
        创建实体
        
        Args:
            novel_id: 小说ID
            entity_id: 实体ID
            name: 实体名称
            entity_type: 实体类型 (character/location/item/organization)
            properties: 属性
            
        Returns:
            entity_id
        """
        properties = properties or {}
        
        if self.storage_type == "neo4j":
            with self.driver.session() as session:
                session.run(
                    """
                    MERGE (e:Entity {id: $entity_id, novel_id: $novel_id})
                    SET e.name = $name,
                        e.type = $entity_type,
                        e += $properties
                    """,
                    entity_id=entity_id,
                    novel_id=novel_id,
                    name=name,
                    entity_type=entity_type,
                    properties=properties
                )
        else:
            entity = Entity(
                id=entity_id,
                name=name,
                entity_type=entity_type,
                properties={"novel_id": novel_id, **properties}
            )
            self.entities[entity_id] = entity
        
        return entity_id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """获取实体"""
        if self.storage_type == "neo4j":
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (e:Entity {id: $entity_id})
                    RETURN e.id as id, e.name as name, e.type as type, e as properties
                    """,
                    entity_id=entity_id
                )
                record = result.single()
                if record:
                    properties = dict(record["properties"])
                    del properties["id"]
                    del properties["name"]
                    del properties["type"]
                    return Entity(
                        id=record["id"],
                        name=record["name"],
                        entity_type=record["type"],
                        properties=properties
                    )
        else:
            return self.entities.get(entity_id)
        
        return None
    
    # ==================== Relationship Operations ====================
    
    def create_relationship(
        self,
        novel_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """
        创建关系
        
        Args:
            novel_id: 小说ID
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            properties: 关系属性
            
        Returns:
            是否成功
        """
        properties = properties or {}
        
        if self.storage_type == "neo4j":
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (a:Entity {id: $source_id, novel_id: $novel_id})
                    MATCH (b:Entity {id: $target_id, novel_id: $novel_id})
                    MERGE (a)-[r:RELATES {type: $relation_type}]->(b)
                    SET r += $properties
                    """,
                    source_id=source_id,
                    target_id=target_id,
                    novel_id=novel_id,
                    relation_type=relation_type,
                    properties=properties
                )
        else:
            # 检查实体是否存在
            if source_id not in self.entities or target_id not in self.entities:
                return False
            
            rel = Relationship(
                source=source_id,
                target=target_id,
                relation_type=relation_type,
                properties={"novel_id": novel_id, **properties}
            )
            self.relationships.append(rel)
        
        return True
    
    def query_relationships(
        self,
        novel_id: str,
        entity_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both"  # out/in/both
    ) -> List[Dict[str, Any]]:
        """
        查询实体关系
        
        Args:
            novel_id: 小说ID
            entity_id: 实体ID
            relation_type: 关系类型过滤
            direction: 方向
            
        Returns:
            关系列表
        """
        results = []
        
        if self.storage_type == "neo4j":
            with self.driver.session() as session:
                if direction == "out":
                    query = """
                        MATCH (a:Entity {id: $entity_id, novel_id: $novel_id})
                              -[r:RELATES]->(b:Entity {novel_id: $novel_id})
                    """
                elif direction == "in":
                    query = """
                        MATCH (a:Entity {novel_id: $novel_id})
                              -[r:RELATES]->(b:Entity {id: $entity_id, novel_id: $novel_id})
                    """
                else:
                    query = """
                        MATCH (a:Entity {id: $entity_id, novel_id: $novel_id})
                              -[r:RELATES]-(b:Entity {novel_id: $novel_id})
                    """
                
                if relation_type:
                    query += " WHERE r.type = $relation_type"
                
                query += " RETURN a.name as source, b.name as target, r.type as relation, r as properties"
                
                result = session.run(
                    query,
                    entity_id=entity_id,
                    novel_id=novel_id,
                    relation_type=relation_type
                )
                
                for record in result:
                    props = dict(record["properties"])
                    del props["type"]
                    results.append({
                        "source": record["source"],
                        "target": record["target"],
                        "relation": record["relation"],
                        "properties": props
                    })
        else:
            # 内存查询
            for rel in self.relationships:
                if rel.properties.get("novel_id") != novel_id:
                    continue
                
                if relation_type and rel.relation_type != relation_type:
                    continue
                
                match = False
                if direction in ["out", "both"] and rel.source == entity_id:
                    match = True
                if direction in ["in", "both"] and rel.target == entity_id:
                    match = True
                
                if match:
                    source_entity = self.entities.get(rel.source)
                    target_entity = self.entities.get(rel.target)
                    if source_entity and target_entity:
                        results.append({
                            "source": source_entity.name,
                            "target": target_entity.name,
                            "relation": rel.relation_type,
                            "properties": {k: v for k, v in rel.properties.items() if k != "novel_id"}
                        })
        
        return results
    
    def find_path(
        self,
        novel_id: str,
        source_id: str,
        target_id: str,
        max_depth: int = 3
    ) -> List[List[Dict[str, Any]]]:
        """
        查找两个实体之间的路径
        
        Args:
            novel_id: 小说ID
            source_id: 源实体
            target_id: 目标实体
            max_depth: 最大深度
            
        Returns:
            路径列表
        """
        if self.storage_type == "neo4j":
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH path = shortestPath(
                        (a:Entity {id: $source_id, novel_id: $novel_id})
                        -[:RELATES*1..$max_depth]-
                        (b:Entity {id: $target_id, novel_id: $novel_id})
                    )
                    RETURN path
                    """,
                    source_id=source_id,
                    target_id=target_id,
                    novel_id=novel_id,
                    max_depth=max_depth
                )
                
                paths = []
                for record in result:
                    path = record["path"]
                    path_data = []
                    for rel in path.relationships:
                        path_data.append({
                            "source": rel.start_node["name"],
                            "target": rel.end_node["name"],
                            "relation": rel["type"]
                        })
                    paths.append(path_data)
                return paths
        else:
            # 内存中使用 BFS
            return self._bfs_path(source_id, target_id, max_depth, novel_id)
    
    def _bfs_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int,
        novel_id: str
    ) -> List[List[Dict[str, Any]]]:
        """BFS 查找路径"""
        from collections import deque
        
        queue = deque([(source_id, [])])
        visited = {source_id}
        paths = []
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
            
            if current == target_id and path:
                paths.append(path)
                continue
            
            # 查找相邻节点
            for rel in self.relationships:
                if rel.properties.get("novel_id") != novel_id:
                    continue
                
                next_node = None
                if rel.source == current:
                    next_node = rel.target
                elif rel.target == current:
                    next_node = rel.source
                
                if next_node and next_node not in visited:
                    visited.add(next_node)
                    source_entity = self.entities.get(rel.source)
                    target_entity = self.entities.get(rel.target)
                    if source_entity and target_entity:
                        new_path = path + [{
                            "source": source_entity.name,
                            "target": target_entity.name,
                            "relation": rel.relation_type
                        }]
                        queue.append((next_node, new_path))
        
        return paths
    
    # ==================== Novel Operations ====================
    
    def initialize_novel_graph(self, novel_id: str, story_bible: Dict[str, Any]):
        """
        从小说圣经初始化知识图谱
        
        Args:
            novel_id: 小说ID
            story_bible: 故事圣经
        """
        # 创建角色实体
        characters = story_bible.get("characters", [])
        for char in characters:
            self.create_entity(
                novel_id=novel_id,
                entity_id=f"{novel_id}_char_{char['id']}",
                name=char["name"],
                entity_type="character",
                properties={
                    "age": char.get("age"),
                    "gender": char.get("gender"),
                    "role": char.get("role"),
                    "description": char.get("description")
                }
            )
        
        # 创建角色关系
        for char in characters:
            char_id = f"{novel_id}_char_{char['id']}"
            relationships = char.get("relationships", [])
            for rel in relationships:
                target_id = f"{novel_id}_char_{rel['target_id']}"
                self.create_relationship(
                    novel_id=novel_id,
                    source_id=char_id,
                    target_id=target_id,
                    relation_type=rel["type"],
                    properties={"description": rel.get("description", "")}
                )
        
        # 创建地点实体
        locations = story_bible.get("locations", [])
        for loc in locations:
            self.create_entity(
                novel_id=novel_id,
                entity_id=f"{novel_id}_loc_{loc['id']}",
                name=loc["name"],
                entity_type="location",
                properties={"description": loc.get("description")}
            )
    
    def update_character_state(
        self,
        novel_id: str,
        character_id: str,
        state_updates: Dict[str, Any]
    ):
        """
        更新角色状态
        
        Args:
            novel_id: 小说ID
            character_id: 角色ID
            state_updates: 状态更新
        """
        entity_id = f"{novel_id}_char_{character_id}"
        
        if self.storage_type == "neo4j":
            with self.driver.session() as session:
                set_clause = ", ".join([f"e.{k} = ${k}" for k in state_updates.keys()])
                params = {"entity_id": entity_id, **state_updates}
                session.run(
                    f"""
                    MATCH (e:Entity {{id: $entity_id}})
                    SET {set_clause}
                    """,
                    **params
                )
        else:
            if entity_id in self.entities:
                self.entities[entity_id].properties.update(state_updates)
    
    def get_character_context(
        self,
        novel_id: str,
        character_id: str
    ) -> Dict[str, Any]:
        """
        获取角色上下文（用于写作时参考）
        
        Args:
            novel_id: 小说ID
            character_id: 角色ID
            
        Returns:
            角色上下文
        """
        entity_id = f"{novel_id}_char_{character_id}"
        entity = self.get_entity(entity_id)
        
        if not entity:
            return {}
        
        # 获取关系
        relationships = self.query_relationships(novel_id, entity_id)
        
        return {
            "name": entity.name,
            "properties": entity.properties,
            "relationships": relationships
        }
    
    def clear_novel_graph(self, novel_id: str):
        """清空某小说的图谱"""
        if self.storage_type == "neo4j":
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (e:Entity {novel_id: $novel_id})
                    DETACH DELETE e
                    """,
                    novel_id=novel_id
                )
        else:
            # 删除相关实体和关系
            self.entities = {
                k: v for k, v in self.entities.items()
                if v.properties.get("novel_id") != novel_id
            }
            self.relationships = [
                r for r in self.relationships
                if r.properties.get("novel_id") != novel_id
            ]


# 便捷函数
_kg_instance = None

def get_knowledge_graph() -> KnowledgeGraph:
    """获取知识图谱实例（单例）"""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = KnowledgeGraph()
    return _kg_instance
