"""
User Behavior Logger - 用户使用行为日志
记录用户行为，为未来优化 Agent 策略提供数据支持
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import json
import hashlib


class UserActionType(Enum):
    """用户行为类型"""
    # 创作行为
    CREATE_NOVEL = "create_novel"
    EDIT_CHAPTER = "edit_chapter"
    GENERATE_CONTENT = "generate_content"
    ACCEPT_AI_SUGGESTION = "accept_ai_suggestion"
    REJECT_AI_SUGGESTION = "reject_ai_suggestion"
    MODIFY_AI_OUTPUT = "modify_ai_output"
    
    # 交互行为
    START_WRITERS_ROOM = "start_writers_room"
    INTERVENE_DISCUSSION = "intervene_discussion"
    USE_SKILL = "use_skill"
    APPLY_CONSTRAINT = "apply_constraint"
    
    # 查看行为
    VIEW_STORY_BIBLE = "view_story_bible"
    VIEW_ASSETS = "view_assets"
    VIEW_ANALYTICS = "view_analytics"
    
    # 配置行为
    UPDATE_SETTINGS = "update_settings"
    CONFIGURE_AGENT = "configure_agent"
    
    # 系统行为
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"


class UserSegment(Enum):
    """用户分群"""
    POWER_USER = "power_user"       # 高频深度用户
    REGULAR = "regular"             # 常规用户
    CASUAL = "casual"               # 轻度用户
    NEWBIE = "newbie"               # 新用户
    CHURN_RISK = "churn_risk"       # 流失风险用户


@dataclass
class UserBehaviorEvent:
    """用户行为事件"""
    event_id: str
    user_id: str
    action_type: UserActionType
    session_id: str
    novel_id: Optional[str] = None
    chapter_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "action_type": self.action_type.value,
            "session_id": self.session_id,
            "novel_id": self.novel_id,
            "chapter_id": self.chapter_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class UserSession:
    """用户会话"""
    session_id: str
    user_id: str
    start_time: str
    end_time: Optional[str] = None
    actions: List[UserBehaviorEvent] = field(default_factory=list)
    novel_id: Optional[str] = None
    
    @property
    def duration_seconds(self) -> int:
        """会话持续时间"""
        if not self.end_time:
            return 0
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        return int((end - start).total_seconds())
    
    @property
    def action_count(self) -> int:
        """动作数量"""
        return len(self.actions)


class UserBehaviorLogger:
    """
    用户行为日志记录器
    
    记录用户使用行为，支持：
    1. 行为事件记录
    2. 用户画像构建
    3. 行为模式分析
    4. 用户分群
    """
    
    def __init__(self):
        self.events: List[UserBehaviorEvent] = []
        self.sessions: Dict[str, UserSession] = {}
        self.user_profiles: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_sessions": 0,
            "total_actions": 0,
            "favorite_features": defaultdict(int),
            "writing_patterns": defaultdict(int),
            "last_active": None,
            "segment": UserSegment.NEWBIE
        })
        
        # 行为序列分析
        self.action_sequences: Dict[str, List[str]] = defaultdict(list)
        
        # 性能指标
        self.metrics = {
            "total_events": 0,
            "unique_users": set(),
            "daily_active_users": defaultdict(set),
            "feature_usage": defaultdict(int)
        }
    
    def log_event(
        self,
        user_id: str,
        action_type: UserActionType,
        session_id: str,
        novel_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> UserBehaviorEvent:
        """
        记录用户行为事件
        
        Args:
            user_id: 用户ID
            action_type: 行为类型
            session_id: 会话ID
            novel_id: 小说ID（可选）
            chapter_id: 章节ID（可选）
            metadata: 附加元数据
            
        Returns:
            记录的事件
        """
        event_id = f"evt_{datetime.now().timestamp()}"
        
        event = UserBehaviorEvent(
            event_id=event_id,
            user_id=user_id,
            action_type=action_type,
            session_id=session_id,
            novel_id=novel_id,
            chapter_id=chapter_id,
            metadata=metadata or {},
            **kwargs
        )
        
        self.events.append(event)
        
        # 更新会话
        if session_id not in self.sessions:
            self.sessions[session_id] = UserSession(
                session_id=session_id,
                user_id=user_id,
                start_time=event.timestamp,
                novel_id=novel_id
            )
        
        self.sessions[session_id].actions.append(event)
        
        # 更新用户画像
        self._update_user_profile(user_id, event)
        
        # 更新指标
        self.metrics["total_events"] += 1
        self.metrics["unique_users"].add(user_id)
        
        today = datetime.now().strftime("%Y-%m-%d")
        self.metrics["daily_active_users"][today].add(user_id)
        self.metrics["feature_usage"][action_type.value] += 1
        
        # 记录行为序列
        self.action_sequences[user_id].append(action_type.value)
        
        return event
    
    def _update_user_profile(self, user_id: str, event: UserBehaviorEvent):
        """更新用户画像"""
        profile = self.user_profiles[user_id]
        
        profile["total_actions"] += 1
        profile["last_active"] = event.timestamp
        profile["favorite_features"][event.action_type.value] += 1
        
        # 识别写作模式
        if event.action_type in [
            UserActionType.GENERATE_CONTENT,
            UserActionType.ACCEPT_AI_SUGGESTION,
            UserActionType.REJECT_AI_SUGGESTION
        ]:
            profile["writing_patterns"][event.action_type.value] += 1
        
        # 更新用户分群
        profile["segment"] = self._determine_user_segment(user_id)
    
    def _determine_user_segment(self, user_id: str) -> UserSegment:
        """确定用户分群"""
        profile = self.user_profiles[user_id]
        
        total_actions = profile["total_actions"]
        days_since_last_active = self._days_since(profile["last_active"])
        
        # 流失风险用户：7天未活跃
        if days_since_last_active > 7:
            return UserSegment.CHURN_RISK
        
        # 新用户：少于10个动作
        if total_actions < 10:
            return UserSegment.NEWBIE
        
        # 轻度用户：少于50个动作
        if total_actions < 50:
            return UserSegment.CASUAL
        
        # 深度用户：超过200个动作且经常使用高级功能
        if total_actions > 200:
            advanced_usage = sum(
                profile["favorite_features"].get(f, 0)
                for f in ["start_writers_room", "use_skill", "configure_agent"]
            )
            if advanced_usage > 10:
                return UserSegment.POWER_USER
        
        return UserSegment.REGULAR
    
    def _days_since(self, timestamp: Optional[str]) -> int:
        """计算距离今天的天数"""
        if not timestamp:
            return 999
        
        last_active = datetime.fromisoformat(timestamp)
        now = datetime.now()
        return (now - last_active).days
    
    def end_session(self, session_id: str):
        """结束会话"""
        if session_id in self.sessions:
            self.sessions[session_id].end_time = datetime.now().isoformat()
            
            # 更新用户会话数
            user_id = self.sessions[session_id].user_id
            self.user_profiles[user_id]["total_sessions"] += 1
    
    def get_user_behavior_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户行为摘要"""
        profile = self.user_profiles.get(user_id, {})
        
        # 获取用户事件
        user_events = [e for e in self.events if e.user_id == user_id]
        
        # 计算行为统计
        action_distribution = defaultdict(int)
        hourly_distribution = defaultdict(int)
        
        for event in user_events:
            action_distribution[event.action_type.value] += 1
            
            hour = datetime.fromisoformat(event.timestamp).hour
            hourly_distribution[hour] += 1
        
        # 活跃时间段
        peak_hours = sorted(
            hourly_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            "user_id": user_id,
            "segment": profile.get("segment", UserSegment.NEWBIE).value,
            "total_actions": profile.get("total_actions", 0),
            "total_sessions": profile.get("total_sessions", 0),
            "last_active": profile.get("last_active"),
            "favorite_features": dict(profile.get("favorite_features", {})),
            "action_distribution": dict(action_distribution),
            "peak_active_hours": [h[0] for h in peak_hours],
            "writing_behavior": self._analyze_writing_behavior(user_id)
        }
    
    def _analyze_writing_behavior(self, user_id: str) -> Dict[str, Any]:
        """分析用户写作行为"""
        user_events = [e for e in self.events if e.user_id == user_id]
        
        # AI 接受率
        ai_suggestions = [
            e for e in user_events
            if e.action_type in [
                UserActionType.ACCEPT_AI_SUGGESTION,
                UserActionType.REJECT_AI_SUGGESTION
            ]
        ]
        
        accept_count = sum(
            1 for e in ai_suggestions
            if e.action_type == UserActionType.ACCEPT_AI_SUGGESTION
        )
        
        accept_rate = accept_count / len(ai_suggestions) if ai_suggestions else 0
        
        # 修改频率
        modify_count = sum(
            1 for e in user_events
            if e.action_type == UserActionType.MODIFY_AI_OUTPUT
        )
        
        generate_count = sum(
            1 for e in user_events
            if e.action_type == UserActionType.GENERATE_CONTENT
        )
        
        modify_rate = modify_count / generate_count if generate_count else 0
        
        return {
            "ai_accept_rate": round(accept_rate, 3),
            "ai_modify_rate": round(modify_rate, 3),
            "prefers_manual_edit": modify_rate > 0.5,
            "trusts_ai_suggestions": accept_rate > 0.7
        }
    
    def get_behavior_patterns(self) -> Dict[str, Any]:
        """获取整体行为模式"""
        # 常用功能排行
        feature_ranking = sorted(
            self.metrics["feature_usage"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # 用户分群分布
        segment_distribution = defaultdict(int)
        for profile in self.user_profiles.values():
            segment_distribution[profile["segment"].value] += 1
        
        # 行为序列模式（找出最常见的3步行为序列）
        common_sequences = self._find_common_sequences(3)
        
        return {
            "total_unique_users": len(self.metrics["unique_users"]),
            "total_events": self.metrics["total_events"],
            "feature_ranking": feature_ranking,
            "segment_distribution": dict(segment_distribution),
            "common_behavior_sequences": common_sequences,
            "daily_active_users": {
                date: len(users)
                for date, users in sorted(self.metrics["daily_active_users"].items())[-7:]
            }
        }
    
    def _find_common_sequences(self, length: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """查找常见的行为序列"""
        sequence_counts = defaultdict(int)
        
        for user_id, actions in self.action_sequences.items():
            if len(actions) < length:
                continue
            
            for i in range(len(actions) - length + 1):
                sequence = tuple(actions[i:i+length])
                sequence_counts[sequence] += 1
        
        # 返回最常见的序列
        top_sequences = sorted(
            sequence_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return [
            {
                "sequence": list(seq),
                "count": count,
                "description": self._describe_sequence(list(seq))
            }
            for seq, count in top_sequences
        ]
    
    def _describe_sequence(self, sequence: List[str]) -> str:
        """描述行为序列"""
        descriptions = {
            "create_novel": "创建小说",
            "edit_chapter": "编辑章节",
            "generate_content": "生成内容",
            "accept_ai_suggestion": "接受AI建议",
            "reject_ai_suggestion": "拒绝AI建议",
            "modify_ai_output": "修改AI输出",
            "start_writers_room": "启动Writers Room",
            "intervene_discussion": "干预讨论",
            "use_skill": "使用技能",
            "view_story_bible": "查看Story Bible",
            "view_assets": "查看资产"
        }
        
        return " -> ".join(descriptions.get(a, a) for a in sequence)
    
    def generate_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """生成优化建议"""
        suggestions = []
        
        patterns = self.get_behavior_patterns()
        
        # 分析 AI 接受率
        total_accepts = self.metrics["feature_usage"].get("accept_ai_suggestion", 0)
        total_rejects = self.metrics["feature_usage"].get("reject_ai_suggestion", 0)
        
        if total_accepts + total_rejects > 0:
            accept_rate = total_accepts / (total_accepts + total_rejects)
            
            if accept_rate < 0.5:
                suggestions.append({
                    "priority": "high",
                    "area": "ai_quality",
                    "issue": "AI建议接受率过低",
                    "current_rate": round(accept_rate, 3),
                    "suggestion": "优化AI生成质量，增加审核步骤",
                    "expected_impact": "提升用户满意度和创作效率"
                })
        
        # 分析功能使用情况
        if patterns["feature_ranking"]:
            top_feature = patterns["feature_ranking"][0]
            if top_feature[1] / self.metrics["total_events"] > 0.5:
                suggestions.append({
                    "priority": "medium",
                    "area": "feature_diversity",
                    "issue": "用户过度依赖单一功能",
                    "dominant_feature": top_feature[0],
                    "suggestion": "引导用户尝试其他功能，如Writers Room、Story Bible等",
                    "expected_impact": "提升用户粘性和功能使用率"
                })
        
        # 分析用户流失
        churn_risk_count = sum(
            1 for p in self.user_profiles.values()
            if p["segment"] == UserSegment.CHURN_RISK
        )
        
        if churn_risk_count > len(self.user_profiles) * 0.2:
            suggestions.append({
                "priority": "high",
                "area": "user_retention",
                "issue": "流失风险用户比例过高",
                "churn_risk_users": churn_risk_count,
                "suggestion": "实施用户召回策略，发送个性化推荐和更新通知",
                "expected_impact": "降低用户流失率"
            })
        
        return suggestions
    
    def export_data(self, format: str = "json") -> str:
        """导出行为数据"""
        data = {
            "export_time": datetime.now().isoformat(),
            "total_events": len(self.events),
            "total_users": len(self.user_profiles),
            "behavior_patterns": self.get_behavior_patterns(),
            "optimization_suggestions": self.generate_optimization_suggestions()
        }
        
        if format == "json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        
        return str(data)


# 全局实例
_behavior_logger: Optional[UserBehaviorLogger] = None


def get_behavior_logger() -> UserBehaviorLogger:
    """获取用户行为日志记录器实例"""
    global _behavior_logger
    if _behavior_logger is None:
        _behavior_logger = UserBehaviorLogger()
    return _behavior_logger
