"""
Advanced Features API - 高级功能API
包含：
1. 增强记忆系统
2. 原创性追踪
3. 洗稿检测
4. 符号逻辑约束
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.memory.enhanced_memory import get_enhanced_memory, MemoryTier
from app.core.originality_tracker import (
    get_originality_analyzer, 
    get_certificate_generator,
    ContentSourceType
)
from app.core.plagiarism_detector import get_plagiarism_detector
from app.core.symbolic_logic_engine import (
    get_symbolic_logic_engine,
    RuleType,
    LogicPredicate,
    FactAssertion,
    WorldRule
)

router = APIRouter(prefix="/api/advanced", tags=["advanced-features"])


# ========== 增强记忆系统 API ==========

class IndexChapterRequest(BaseModel):
    novel_id: str
    chapter_id: str
    chapter_content: str
    chapter_summary: str
    key_events: List[Dict[str, Any]]


class GetContextRequest(BaseModel):
    novel_id: str
    current_chapter: int
    query: str
    character_ids: Optional[List[str]] = None


@router.post("/memory/index-chapter")
async def index_chapter(request: IndexChapterRequest):
    """索引章节内容到增强记忆系统"""
    try:
        memory = get_enhanced_memory()
        await memory.index_chapter(
            novel_id=request.novel_id,
            chapter_id=request.chapter_id,
            chapter_content=request.chapter_content,
            chapter_summary=request.chapter_summary,
            key_events=request.key_events
        )
        return {"message": "Chapter indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/get-context")
async def get_enhanced_context(request: GetContextRequest):
    """获取增强的写作上下文"""
    try:
        memory = get_enhanced_memory()
        context = await memory.get_enhanced_context(
            novel_id=request.novel_id,
            current_chapter=request.current_chapter,
            query=request.query,
            character_ids=request.character_ids
        )
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 原创性追踪 API ==========

class AddSegmentRequest(BaseModel):
    novel_id: str
    content: str
    source_type: str  # user_input, ai_generated, ai_edited, user_edited_ai
    chapter_id: Optional[str] = None
    author_id: Optional[str] = None
    parent_segment_id: Optional[str] = None


@router.post("/originality/add-segment")
async def add_content_segment(request: AddSegmentRequest):
    """添加内容片段用于原创性分析"""
    try:
        analyzer = get_originality_analyzer()
        
        source_type = ContentSourceType(request.source_type)
        
        segment_id = analyzer.add_segment(
            novel_id=request.novel_id,
            content=request.content,
            source_type=source_type,
            chapter_id=request.chapter_id,
            author_id=request.author_id,
            parent_segment_id=request.parent_segment_id
        )
        
        return {"segment_id": segment_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/originality/analyze/{novel_id}")
async def analyze_originality(novel_id: str, chapter_id: Optional[str] = None):
    """分析小说或章节的原创性"""
    try:
        analyzer = get_originality_analyzer()
        report = analyzer.analyze_originality(novel_id, chapter_id)
        return report.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/originality/statistics/{novel_id}")
async def get_novel_statistics(novel_id: str):
    """获取小说原创性统计"""
    try:
        analyzer = get_originality_analyzer()
        stats = analyzer.get_novel_statistics(novel_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/originality/certificate/{novel_id}")
async def generate_originality_certificate(novel_id: str):
    """生成原创性证书"""
    try:
        analyzer = get_originality_analyzer()
        cert_generator = get_certificate_generator()
        certificate = cert_generator.generate_certificate(novel_id, analyzer)
        return certificate
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 洗稿检测 API ==========

class PlagiarismCheckRequest(BaseModel):
    text: str
    text_id: str
    check_sensitive: bool = True
    check_similarity: bool = True


@router.post("/plagiarism/check")
async def check_plagiarism(request: PlagiarismCheckRequest):
    """执行洗稿检测"""
    try:
        detector = get_plagiarism_detector()
        report = await detector.detect(
            text=request.text,
            text_id=request.text_id,
            check_sensitive=request.check_sensitive,
            check_similarity=request.check_similarity
        )
        return report.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plagiarism/stats")
async def get_plagiarism_stats():
    """获取检测统计"""
    try:
        detector = get_plagiarism_detector()
        stats = detector.get_detection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 符号逻辑约束 API ==========

class CreateRuleRequest(BaseModel):
    rule_type: str
    name: str
    description: str
    config: Dict[str, Any]


class AssertFactRequest(BaseModel):
    fact_id: str
    predicate_name: str
    arguments: List[str]
    source: str
    confidence: float = 1.0


class ValidateChapterRequest(BaseModel):
    chapter_content: str
    chapter_id: str


@router.post("/logic/create-magic-rule")
async def create_magic_system_rule(request: CreateRuleRequest):
    """创建魔法系统规则"""
    try:
        engine = get_symbolic_logic_engine()
        
        rule = engine.create_magic_system_rule(
            rule_id=f"rule_{request.name}_{hash(request.description) % 10000}",
            name=request.name,
            description=request.description,
            magic_levels=request.config.get("magic_levels", []),
            level_requirements=request.config.get("level_requirements", {})
        )
        
        rule_id = engine.add_rule(rule)
        
        return {"rule_id": rule_id, "rule": rule.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logic/create-power-rule")
async def create_power_level_rule(request: CreateRuleRequest):
    """创建战力等级规则"""
    try:
        engine = get_symbolic_logic_engine()
        
        rule = engine.create_power_level_rule(
            rule_id=f"rule_{request.name}_{hash(request.description) % 10000}",
            name=request.name,
            description=request.description,
            power_tiers=request.config.get("power_tiers", [])
        )
        
        rule_id = engine.add_rule(rule)
        
        return {"rule_id": rule_id, "rule": rule.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logic/assert-fact")
async def assert_fact(request: AssertFactRequest):
    """断言事实"""
    try:
        engine = get_symbolic_logic_engine()
        
        fact = FactAssertion(
            fact_id=request.fact_id,
            predicate=LogicPredicate(
                name=request.predicate_name,
                arguments=request.arguments
            ),
            source=request.source,
            confidence=request.confidence
        )
        
        success = engine.assert_fact(fact)
        
        return {
            "success": success,
            "fact_id": request.fact_id,
            "violations": [
                {
                    "rule_name": v.rule_name,
                    "severity": v.severity,
                    "suggestion": v.suggested_fix
                }
                for v in engine.violations[-5:]  # 最近5个违规
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logic/validate-chapter")
async def validate_chapter(request: ValidateChapterRequest):
    """验证章节内容"""
    try:
        engine = get_symbolic_logic_engine()
        result = engine.validate_chapter_content(
            chapter_content=request.chapter_content,
            chapter_id=request.chapter_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logic/consistency-report")
async def get_consistency_report():
    """获取世界观一致性报告"""
    try:
        engine = get_symbolic_logic_engine()
        report = engine.get_world_consistency_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logic/rules")
async def get_all_rules():
    """获取所有规则"""
    try:
        engine = get_symbolic_logic_engine()
        rules = [rule.to_dict() for rule in engine.rules.values()]
        return {"rules": rules, "total": len(rules)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
