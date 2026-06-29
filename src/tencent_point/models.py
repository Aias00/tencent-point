"""数据模型定义"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UserInfo:
    """用户基本信息（嵌套在排行数据中）"""

    uid: int = 0
    nickname: str = ""
    avatar: str = ""
    level: int = 0
    growth: int = 0
    privilege: int = 0
    company: str = ""
    title: str = ""
    introduce: str = ""
    article_num: int = 0
    article_read_num: int = 0
    article_fav_num: int = 0
    be_concern_user_num: int = 0
    medals: list = field(default_factory=list)


@dataclass
class RankEntry:
    """热力值排行条目"""

    rank: int = 0
    user: UserInfo = field(default_factory=UserInfo)
    total_score: float = 0
    creative_score: float = 0
    read_score: float = 0
    interactive_score: float = 0
    article_count: int = 0
    active_month: int = 0
    cur_month_article_count: int = 0
    read_num: int = 0
    like_num: int = 0
    fav_num: int = 0
    yesterday_rank: Optional[int] = None


@dataclass
class ValuableAuthor:
    """最具价值作者排行条目"""

    rank: int = 0
    user: UserInfo = field(default_factory=UserInfo)
    score: float = 0
    quality_score: float = 0
    influence_score: float = 0
    activity_score: float = 0
    factor: float = 1.0


@dataclass
class UserRank:
    """用户排名数据（来自 /api/user/rank）"""

    rank: int = 0
    user: UserInfo = field(default_factory=UserInfo)
    total_score: float = 0
    creative_score: float = 0
    read_score: float = 0
    interactive_score: float = 0
    article_count: int = 0
    active_month: int = 0
    cur_month_article_count: int = 0
    read_num: int = 0
    like_num: int = 0
    fav_num: int = 0


@dataclass
class UserDetail:
    """用户详情数据（来自 /api/user/detail）"""

    uid: int = 0
    nickname: str = ""
    avatar: str = ""
    level: int = 0
    growth: int = 0
    privilege: int = 0
    article_num: int = 0
    article_read_num: int = 0
    article_fav_num: int = 0
    article_like_num: int = 0
    article_comment_num: int = 0
    article_recomm_num: int = 0
    be_concern_user_num: int = 0
    answer_num: int = 0
    ask_num: int = 0
    company: str = ""
    title: str = ""
    introduce: str = ""
    is_original_author: int = 0
    join_column_num: int = 0


@dataclass
class TopicSuggestion:
    """选题推荐"""

    topic: str = ""
    angle: str = ""
    rationale: str = ""
    expected_impact: str = ""
    reference_authors: List[str] = field(default_factory=list)
    difficulty: str = ""  # 简单 / 中等 / 困难


@dataclass
class CompetitorInsight:
    """竞品分析洞察"""

    dimension: str = ""
    your_value: str = ""
    top_avg_value: str = ""
    gap: str = ""
    suggestion: str = ""


@dataclass
class ActionItem:
    """行动计划条目"""

    priority: int = 0
    title: str = ""
    current: str = ""
    target: str = ""
    expected_impact: str = ""
    action: str = ""


@dataclass
class ScoreDistribution:
    """分值构成分析"""

    avg_creative_ratio: float = 0
    avg_read_ratio: float = 0
    avg_interactive_ratio: float = 0
    avg_creative_score: float = 0
    avg_read_score: float = 0
    avg_interactive_score: float = 0
    avg_total_score: float = 0
    avg_articles_per_month: float = 0
    avg_reads_per_article: float = 0
    avg_likes_per_article: float = 0
    avg_favs_per_article: float = 0
    avg_interactive_rate: float = 0  # (likes + favs) / reads
    avg_active_month: float = 0


@dataclass
class FrequencyGroup:
    """按活跃月数分组的统计"""

    active_month: int = 0
    count: int = 0
    avg_total_score: float = 0
    avg_creative_score: float = 0
    avg_read_score: float = 0
    avg_interactive_score: float = 0
    avg_article_count: float = 0
