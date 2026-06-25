"""选题推荐模块"""

from __future__ import annotations

from typing import Dict, List, Optional

from .models import (
    FrequencyGroup,
    RankEntry,
    ScoreDistribution,
    TopicSuggestion,
    UserDetail,
    UserRank,
)
from .competitor_analysis import analyze_score_distribution, calculate_frequency_groups


def analyze_engagement_patterns(entries: List[RankEntry]) -> Dict[str, float]:
    """分析互动模式，返回关键互动指标"""
    if not entries:
        return {}

    like_read_ratios = []
    fav_read_ratios = []
    creative_ratios = []
    read_ratios = []
    interactive_ratios = []

    for e in entries:
        total = e.total_score or 1
        creative_ratios.append(e.creative_score / total)
        read_ratios.append(e.read_score / total)
        interactive_ratios.append(e.interactive_score / total)

        if e.read_num > 0:
            like_read_ratios.append(e.like_num / e.read_num)
            fav_read_ratios.append(e.fav_num / e.read_num)

    return {
        "avg_like_read_ratio": _avg(like_read_ratios),
        "avg_fav_read_ratio": _avg(fav_read_ratios),
        "avg_creative_ratio": _avg(creative_ratios),
        "avg_read_ratio": _avg(read_ratios),
        "avg_interactive_ratio": _avg(interactive_ratios),
        # 高互动文章特征
        "high_interactive_threshold": _percentile(interactive_ratios, 75),
        "high_read_threshold": _percentile(read_ratios, 75),
    }


def identify_low_hanging_fruit(
    user_rank: Optional[UserRank],
    distribution: ScoreDistribution,
    engagement: Dict[str, float],
) -> List[str]:
    """识别最低成本提升方向"""
    fruits = []

    if user_rank is None:
        return ["发布更多原创文章以获取创作分", "选择热门选题以提升阅读分", "增加实操内容以提升互动分"]

    total = user_rank.total_score or 1
    user_creative_ratio = user_rank.creative_score / total
    user_read_ratio = user_rank.read_score / total
    user_interactive_ratio = user_rank.interactive_score / total

    # 找出用户占比最低的维度
    ratios = [
        ("创作分", user_creative_ratio, distribution.avg_creative_ratio),
        ("阅读分", user_read_ratio, distribution.avg_read_ratio),
        ("互动分", user_interactive_ratio, distribution.avg_interactive_ratio),
    ]

    # 按低于平均值的程度排序
    below_avg = [(name, user, avg) for name, user, avg in ratios if user < avg]
    below_avg.sort(key=lambda x: x[1] / max(x[2], 0.01))

    for name, user_ratio, avg_ratio in below_avg:
        if name == "创作分":
            fruits.append(f"创作分占比({user_ratio:.0%})低于TOP均值({avg_ratio:.0%})，增加发文量是最直接的提升方式")
        elif name == "阅读分":
            fruits.append(f"阅读分占比({user_ratio:.0%})低于TOP均值({avg_ratio:.0%})，优化选题和标题可快速提升")
        elif name == "互动分":
            fruits.append(f"互动分占比({user_ratio:.0%})低于TOP均值({avg_ratio:.0%})，增加实操案例和互动引导")

    # 如果所有维度都高于平均
    if not below_avg:
        fruits.append("各维度均衡发展，建议全面提升产出量")

    # 活跃月数检查
    if user_rank.active_month < distribution.avg_active_month:
        fruits.append(
            f"活跃月数({user_rank.active_month})低于TOP均值({distribution.avg_active_month:.0f})，"
            f"保持每月发文可提升发文系数加成"
        )

    return fruits


def calculate_optimal_posting_frequency(entries: List[RankEntry]) -> Dict:
    """分析最优发文频率"""
    groups = calculate_frequency_groups(entries)

    if not groups:
        return {"recommendation": "数据不足，建议每月至少发文2篇"}

    # 找出平均热力值最高的活跃月数组
    best_group = max(groups, key=lambda g: g.avg_total_score)

    # 计算边际收益（每增加1个活跃月的热力值增量）
    marginal_gains = []
    sorted_groups = sorted(groups, key=lambda g: g.active_month)
    for i in range(1, len(sorted_groups)):
        gain = sorted_groups[i].avg_total_score - sorted_groups[i - 1].avg_total_score
        marginal_gains.append(
            {
                "from_month": sorted_groups[i - 1].active_month,
                "to_month": sorted_groups[i].active_month,
                "gain": gain,
                "avg_articles": sorted_groups[i].avg_article_count,
            }
        )

    # 推荐发文频率
    if best_group.active_month >= 5:
        recommendation = f"活跃{best_group.active_month}个月的作者平均热力值最高({best_group.avg_total_score:.0f})，建议全年保持每月至少发文1篇"
    elif best_group.active_month >= 3:
        recommendation = f"活跃{best_group.active_month}个月的作者表现最好，建议至少保持3个月以上的连续活跃"
    else:
        recommendation = "保持每月发文以获得发文系数加成，活跃月数越多乘数越高"

    return {
        "frequency_groups": groups,
        "best_active_month": best_group.active_month,
        "best_avg_score": best_group.avg_total_score,
        "marginal_gains": marginal_gains,
        "recommendation": recommendation,
    }


def generate_topic_suggestions(
    distribution: ScoreDistribution,
    categories: List[str],
    user_rank: Optional[UserRank] = None,
    user_detail: Optional[UserDetail] = None,
    top_entries: Optional[List[RankEntry]] = None,
) -> List[TopicSuggestion]:
    """生成选题推荐"""
    suggestions: List[TopicSuggestion] = []

    # 基于用户兴趣领域的选题建议
    category_topics = {
        "云计算": [
            TopicSuggestion(
                topic="云原生架构实战",
                angle="从单体到微服务的迁移踩坑实录，包含完整的K8s部署配置和监控方案",
                rationale=f"TOP作者平均单篇阅读{distribution.avg_reads_per_article:.0f}次，架构类文章通常阅读量更高",
                expected_impact="提升阅读分 + 互动分",
                difficulty="中等",
            ),
            TopicSuggestion(
                topic="Serverless 成本优化指南",
                angle="对比不同场景下Serverless vs 传统部署的成本，附实际账单数据",
                rationale="实用性强、有数据支撑的文章收藏率高，平均收藏率可达5%+",
                expected_impact="提升互动分（收藏）",
                difficulty="简单",
            ),
        ],
        "人工智能": [
            TopicSuggestion(
                topic="LLM 应用开发实战",
                angle="从0到1搭建一个RAG应用，包含代码、部署和优化全流程",
                rationale="AI是当前最热门话题，相关文章阅读量显著高于平均水平",
                expected_impact="大幅提升阅读分",
                difficulty="中等",
            ),
            TopicSuggestion(
                topic="AI 模型部署与推理优化",
                angle="对比vLLM/TGI/Triton等推理框架的性能和部署难度",
                rationale="对比评测类文章互动率高，读者更愿意参与讨论和收藏",
                expected_impact="提升互动分 + 阅读分",
                difficulty="困难",
            ),
        ],
        "后端开发": [
            TopicSuggestion(
                topic="高并发系统设计实战",
                angle="结合腾讯云产品（CKafka/CMQ/TDSQL）的高并发架构案例",
                rationale="腾讯云社区用户偏后端，结合云产品的文章更容易被推荐",
                expected_impact="提升阅读分 + 可能获得官方推荐",
                difficulty="中等",
            ),
            TopicSuggestion(
                topic="Go/Rust 性能优化技巧",
                angle="从pprof/flamegraph到实际优化案例，附带性能对比数据",
                rationale="性能优化类文章收藏率高，是互动分的重要来源",
                expected_impact="提升互动分（收藏）",
                difficulty="中等",
            ),
        ],
        "前端开发": [
            TopicSuggestion(
                topic="React/Vue 3 最新特性深度解析",
                angle="不只是API文档翻译，结合实际项目中的使用场景和踩坑经验",
                rationale="前端文章受众广，但需要差异化才能获得高互动",
                expected_impact="提升阅读分",
                difficulty="简单",
            ),
            TopicSuggestion(
                topic="Web性能优化实战手册",
                angle="Core Web Vitals指标优化全攻略，包含Lighthouse评分从50到95的实践",
                rationale="性能优化是前端永恒话题，实操性强的文章收藏率高",
                expected_impact="提升互动分",
                difficulty="中等",
            ),
        ],
        "数据库": [
            TopicSuggestion(
                topic="MySQL/PostgreSQL 调优实战",
                angle="从慢查询分析到索引优化，附真实SQL执行计划对比",
                rationale="数据库调优是开发者高频需求，搜索流量大",
                expected_impact="持续提升阅读分（长尾流量）",
                difficulty="中等",
            ),
            TopicSuggestion(
                topic="TDSQL vs 自建MySQL 对比评测",
                angle="性能、成本、运维复杂度的多维度对比，附压测数据",
                rationale="结合腾讯云产品的对比评测容易获得官方推荐和额外曝光",
                expected_impact="阅读分 + 可能获得征文加分",
                difficulty="困难",
            ),
        ],
        "DevOps": [
            TopicSuggestion(
                topic="CI/CD 流水线最佳实践",
                angle="从代码提交到生产部署的全自动化流程，含GitHub Actions/腾讯云CODING配置",
                rationale="DevOps实践类文章实用性强，收藏率显著高于平均",
                expected_impact="提升互动分（收藏）",
                difficulty="中等",
            ),
            TopicSuggestion(
                topic="K8s 故障排查手册",
                angle="常见K8s问题及排查流程，附真实故障案例和解决过程",
                rationale="故障排查类文章是长期参考资源，收藏率和长尾阅读量都高",
                expected_impact="持续提升阅读分 + 互动分",
                difficulty="中等",
            ),
        ],
    }

    # 根据用户选择的领域添加选题
    for cat in categories:
        if cat in category_topics:
            # 如果有用户数据，优先推荐最短板对应的选题
            if user_rank:
                total = user_rank.total_score or 1
                user_interactive_ratio = user_rank.interactive_score / total
                user_read_ratio = user_rank.read_score / total

                # 互动分低优先推荐收藏率高的选题
                topics = category_topics[cat]
                if user_interactive_ratio < distribution.avg_interactive_ratio:
                    # 优先推荐中等和困难（深度）的选题
                    topics = sorted(topics, key=lambda t: 0 if "互动" in t.expected_impact else 1)
                elif user_read_ratio < distribution.avg_read_ratio:
                    # 阅读分低优先推荐热门话题
                    topics = sorted(topics, key=lambda t: 0 if "阅读" in t.expected_impact else 1)
                suggestions.extend(topics)
            else:
                suggestions.extend(category_topics[cat])
        else:
            # 未知领域给出通用建议
            suggestions.append(
                TopicSuggestion(
                    topic=f"{cat} 深度实践指南",
                    angle="结合实际项目经验，分享踩坑和优化过程",
                    rationale="深度实践类文章在社区中阅读和互动表现均好于入门类",
                    expected_impact="提升阅读分 + 互动分",
                    difficulty="中等",
                )
            )

    # 添加 TOP 作者参考
    if top_entries:
        top_authors = [e.user.nickname for e in top_entries[:5] if e.user.nickname]
        for s in suggestions:
            if not s.reference_authors:
                s.reference_authors = top_authors[:3]

    return suggestions


def _avg(lst: List[float]) -> float:
    """计算平均值"""
    return sum(lst) / len(lst) if lst else 0


def _percentile(lst: List[float], p: int) -> float:
    """计算百分位数"""
    if not lst:
        return 0
    sorted_lst = sorted(lst)
    idx = int(len(sorted_lst) * p / 100)
    return sorted_lst[min(idx, len(sorted_lst) - 1)]
