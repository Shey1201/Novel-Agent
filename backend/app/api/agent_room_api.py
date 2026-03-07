"""
Agent Room API - AI编剧室API
整合Agent Reasoning、Discussion、Author Decision等功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.core.agent_reasoning_engine import (
    get_agent_reasoning_engine,
    ReasoningContext,
    ReasoningType,
    DecisionType
)
from app.core.agent_discussion_engine import (
    get_agent_discussion_engine,
    DiscussionContext,
    DiscussionRound,
    AgentPersonality
)
from app.core.author_decision_system import (
    get_author_decision_system,
    QuestionType,
    QuestionPriority
)
from app.core.narrative_intelligence_engine import (
    get_narrative_intelligence_engine
)
from app.core.universal_logic_engine import (
    get_universal_logic_engine,
    GenreType
)

router = APIRouter(prefix="/api/agent-room", tags=["agent-room"])


# ========== Agent Reasoning API ==========

class ReasoningRequest(BaseModel):
    novel_id: str
    chapter_id: str
    agent_type: str
    current_scene: str
    story_summary: str
    character_states: Dict[str, Any]
    plot_progress: float
    foreshadowing_status: List[Dict[str, Any]]
    previous_chapters_summary: str
    target_word_count: int = 3000


@router.post("/reasoning")
async def agent_reasoning(request: ReasoningRequest):
    """Agent执行前推理"""
    try:
        engine = get_agent_reasoning_engine()
        
        context = ReasoningContext(
            novel_id=request.novel_id,
            chapter_id=request.chapter_id,
            agent_type=request.agent_type,
            current_scene=request.current_scene,
            story_summary=request.story_summary,
            character_states=request.character_states,
            plot_progress=request.plot_progress,
            foreshadowing_status=request.foreshadowing_status,
            previous_chapters_summary=request.previous_chapters_summary,
            target_word_count=request.target_word_count
        )
        
        result = await engine.reason_before_action(context)
        
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reasoning/history")
async def get_reasoning_history(
    novel_id: Optional[str] = None,
    agent_type: Optional[str] = None
):
    """获取推理历史"""
    try:
        engine = get_agent_reasoning_engine()
        history = engine.get_reasoning_history(novel_id, agent_type)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Agent Discussion API ==========

class StartDiscussionRequest(BaseModel):
    novel_id: str
    chapter_id: str
    topic: str
    current_draft: Optional[str] = None
    author_preferences: Dict[str, Any] = {}
    constraints: Dict[str, Any] = {}
    max_rounds: int = 3


@router.post("/discussion/start")
async def start_discussion(request: StartDiscussionRequest):
    """开始Agent讨论（简化版，返回讨论ID）"""
    try:
        engine = get_agent_discussion_engine()
        
        context = DiscussionContext(
            novel_id=request.novel_id,
            chapter_id=request.chapter_id,
            topic=request.topic,
            current_draft=request.current_draft,
            author_preferences=request.author_preferences,
            constraints=request.constraints
        )
        
        # 生成讨论ID
        import time
        discussion_id = f"disc_{request.novel_id}_{int(time.time())}"
        
        return {
            "discussion_id": discussion_id,
            "status": "started",
            "max_rounds": request.max_rounds,
            "participating_agents": ["planner", "conflict", "writer", "editor", "reader"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discussion/{discussion_id}/round/{round_num}")
async def get_discussion_round(discussion_id: str, round_num: int):
    """获取某轮讨论内容"""
    try:
        engine = get_agent_discussion_engine()
        
        # 模拟返回讨论内容
        rounds = [
            {"round": "planning", "agent": "planner", "personality": "structure", "content": "建议本章重点推进主线剧情，安排关键事件。"},
            {"round": "conflict", "agent": "conflict", "personality": "drama", "content": "这样推进会加快节奏，但可能失去悬念。建议加入误导线索。"},
            {"round": "writing", "agent": "writer", "personality": "literary", "content": "可以用细腻的心理描写来展现角色的内心冲突。"},
            {"round": "editing", "agent": "editor", "personality": "logic", "content": "结构合理，但建议结尾加入悬念，吸引读者继续。"},
            {"round": "reader", "agent": "reader", "personality": "reader", "content": "读者更喜欢反转，这个方向很有吸引力。"}
        ]
        
        if round_num < len(rounds):
            return {"message": rounds[round_num]}
        else:
            return {"message": None, "status": "completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discussion/{discussion_id}/consensus")
async def get_consensus(discussion_id: str):
    """获取讨论共识"""
    try:
        engine = get_agent_discussion_engine()
        consensus = engine.get_consensus_result(discussion_id)
        
        if consensus:
            return consensus
        else:
            # 返回模拟共识
            return {
                "consensus_id": f"consensus_{discussion_id}",
                "status": "reached",
                "consensus_score": 0.75,
                "agreed_points": ["推进主线剧情", "加入心理描写"],
                "disputed_points": [],
                "final_decision": "按讨论结果推进：重点推进主线剧情，同时加入心理描写",
                "requires_author_decision": False,
                "participating_agents": ["planner", "conflict", "writer", "editor", "reader"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Author Decision API ==========

class CreateQuestionRequest(BaseModel):
    novel_id: str
    question_type: str
    priority: str
    title: str
    description: str
    options: List[Dict[str, Any]]
    source_agent: str
    context: Dict[str, Any] = {}
    chapter_id: Optional[str] = None
    blocking: bool = False
    allow_custom: bool = False


class SubmitAnswerRequest(BaseModel):
    question_id: str
    selected_option: str
    custom_answer: Optional[str] = None


@router.post("/decision/question")
async def create_author_question(request: CreateQuestionRequest):
    """创建作者问题"""
    try:
        system = get_author_decision_system()
        
        question_id = system.create_question(
            novel_id=request.novel_id,
            question_type=QuestionType(request.question_type),
            priority=QuestionPriority(request.priority),
            title=request.title,
            description=request.description,
            options=request.options,
            source_agent=request.source_agent,
            context=request.context,
            chapter_id=request.chapter_id,
            blocking=request.blocking,
            allow_custom=request.allow_custom
        )
        
        return {"question_id": question_id, "status": "pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decision/answer")
async def submit_author_answer(request: SubmitAnswerRequest):
    """提交作者回答"""
    try:
        system = get_author_decision_system()
        result = system.submit_answer(
            question_id=request.question_id,
            selected_option=request.selected_option,
            custom_answer=request.custom_answer
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decision/pending")
async def get_pending_questions(
    novel_id: Optional[str] = None,
    priority: Optional[str] = None
):
    """获取待回答的问题"""
    try:
        system = get_author_decision_system()
        
        priority_enum = QuestionPriority(priority) if priority else None
        questions = system.get_pending_questions(novel_id, priority_enum)
        
        return {"questions": questions, "total": len(questions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decision/question/{question_id}")
async def get_question(question_id: str):
    """获取问题详情"""
    try:
        system = get_author_decision_system()
        question = system.get_question(question_id)
        
        if question:
            return question
        else:
            raise HTTPException(status_code=404, detail="Question not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Narrative Intelligence API ==========

class AnalyzeChapterRequest(BaseModel):
    chapter_id: str
    chapter_number: int
    content: str


class AddPlotNodeRequest(BaseModel):
    novel_id: str
    node_type: str
    name: str
    description: str
    chapter_introduced: str
    metadata: Dict[str, Any] = {}


class AddPlotEdgeRequest(BaseModel):
    novel_id: str
    source: str
    target: str
    edge_type: str
    weight: float = 1.0
    description: str = ""
    chapter_formed: str = ""


@router.post("/narrative/analyze-chapter")
async def analyze_chapter_structure(request: AnalyzeChapterRequest):
    """分析章节结构"""
    try:
        engine = get_narrative_intelligence_engine()
        structure = engine.analyze_chapter_structure(
            chapter_id=request.chapter_id,
            chapter_number=request.chapter_number,
            content=request.content
        )
        
        return structure.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/narrative/plot-node")
async def add_plot_node(request: AddPlotNodeRequest):
    """添加剧情节点"""
    try:
        engine = get_narrative_intelligence_engine()
        from app.core.narrative_intelligence_engine import PlotNode, PlotNodeType
        
        plot_graph = engine.get_or_create_plot_graph(request.novel_id)
        
        node = PlotNode(
            id=f"node_{request.name}_{hash(request.description) % 10000}",
            node_type=PlotNodeType(request.node_type),
            name=request.name,
            description=request.description,
            chapter_introduced=request.chapter_introduced,
            metadata=request.metadata
        )
        
        node_id = plot_graph.add_node(node)
        
        return {"node_id": node_id, "node": node.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/narrative/plot-edge")
async def add_plot_edge(request: AddPlotEdgeRequest):
    """添加剧情边"""
    try:
        engine = get_narrative_intelligence_engine()
        from app.core.narrative_intelligence_engine import PlotEdge, PlotEdgeType
        
        plot_graph = engine.get_or_create_plot_graph(request.novel_id)
        
        edge = PlotEdge(
            source=request.source,
            target=request.target,
            edge_type=PlotEdgeType(request.edge_type),
            weight=request.weight,
            description=request.description,
            chapter_formed=request.chapter_formed
        )
        
        success = plot_graph.add_edge(edge)
        
        return {"success": success, "edge": edge.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/narrative/report/{novel_id}")
async def get_narrative_report(novel_id: str):
    """获取叙事报告"""
    try:
        engine = get_narrative_intelligence_engine()
        report = engine.get_narrative_report(novel_id)
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/narrative/character-arc/{novel_id}/{character_id}")
async def get_character_arc(novel_id: str, character_id: str):
    """获取角色弧线"""
    try:
        engine = get_narrative_intelligence_engine()
        plot_graph = engine.get_or_create_plot_graph(novel_id)
        arc = plot_graph.get_character_arc(character_id)
        
        return {"character_id": character_id, "arc": arc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Foreshadowing API ==========

class PlantForeshadowingRequest(BaseModel):
    novel_id: str
    clue: str
    chapter: str
    priority: str = "medium"
    related_characters: List[str] = []
    expected_resolution: str = ""


class ResolveForeshadowingRequest(BaseModel):
    fs_id: str
    chapter: str
    resolution: str


@router.post("/foreshadowing/plant")
async def plant_foreshadowing(request: PlantForeshadowingRequest):
    """埋下伏笔"""
    try:
        engine = get_narrative_intelligence_engine()
        fs_id = engine.foreshadowing_engine.plant_foreshadowing(
            novel_id=request.novel_id,
            clue=request.clue,
            chapter=request.chapter,
            priority=request.priority,
            related_characters=request.related_characters,
            expected_resolution=request.expected_resolution
        )
        
        return {"foreshadowing_id": fs_id, "status": "planted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/foreshadowing/resolve")
async def resolve_foreshadowing(request: ResolveForeshadowingRequest):
    """解决伏笔"""
    try:
        engine = get_narrative_intelligence_engine()
        success = engine.foreshadowing_engine.resolve_foreshadowing(
            fs_id=request.fs_id,
            chapter=request.chapter,
            resolution=request.resolution
        )
        
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/foreshadowing/unresolved/{novel_id}")
async def get_unresolved_foreshadowings(
    novel_id: str,
    min_priority: str = "medium"
):
    """获取未解决的伏笔"""
    try:
        engine = get_narrative_intelligence_engine()
        unresolved = engine.foreshadowing_engine.get_unresolved_foreshadowings(
            novel_id=novel_id,
            min_priority=min_priority
        )
        
        return {"foreshadowings": unresolved, "count": len(unresolved)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/foreshadowing/report/{novel_id}")
async def get_foreshadowing_report(novel_id: str):
    """获取伏笔报告"""
    try:
        engine = get_narrative_intelligence_engine()
        report = engine.foreshadowing_engine.get_foreshadowing_report(novel_id)
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Universal Logic API ==========

class ValidateContentRequest(BaseModel):
    content: str
    content_id: str
    genre: str = "general"
    extract_facts: bool = True


@router.post("/logic/validate")
async def validate_content_logic(request: ValidateContentRequest):
    """验证内容逻辑"""
    try:
        engine = get_universal_logic_engine(GenreType(request.genre))
        result = engine.validate_content(
            content=request.content,
            content_id=request.content_id,
            extract_facts=request.extract_facts
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logic/consistency-report/{novel_id}")
async def get_logic_consistency_report(novel_id: str, genre: str = "general"):
    """获取逻辑一致性报告"""
    try:
        engine = get_universal_logic_engine(GenreType(genre))
        report = engine.get_consistency_report()
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
