"""竞品分析模块"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .models import (
    ActionItem,
    CompetitorInsight,
    FrequencyGroup,
    RankEntry,
    ScoreDistribution,
    UserDetail,
    UserRank,
)


def analyze_score_distribution(entries: List[RankEntry]) -> ScoreDistribution:
    """计算 Top 作者的平均分值构成"""
    if not entries:
        return ScoreDistribution()

    n = len(entries)
    total_creative = sum(e.creative_score for e in entries)
    total_read = sum(e.read_score for e in entries)
    total_interactive = sum(e.interactive_score for e in entries)
    total_score = sum(e.total_score for e in entries)

    avg_total = total_score / n
    avg_creative = total_creative / n
    avg_read = total_read / n
    avg_interactive = total_interactive / n

    # 避免除零
    total_sum = avg_creative + avg_read + avg_interactive
    if total_sum == 0:
        total_sum = 1

    # 按文章数和活跃月数计算平均
    articles_per_month_list = []
    reads_per_article_list = []
    likes_per_article_list = []
    favs_per_article_list = []
    interactive_rate_list = []
    active_months = []

    for e in entries:
        if e.active_month > 0:
            articles_per_month_list.append(e.article_count / e.active_month)
        if e.article_count > 0:
            reads_per_article_list.append(e.read_num / e.article_count)
            likes_per_article_list.append(e.like_num / e.article_count)
            favs_per_article_list.append(e.fav_num / e.article_count)
        if e.read_num > 0:
            interactive_rate_list.append(
                (e.like_num + e.fav_num) / e.read_num
            )
        active_months.append(e.active_month)

    return ScoreDistribution(
        avg_creative_ratio=avg_creative / total_sum,
        avg_read_ratio=avg_read / total_sum,
        avg_interactive_ratio=avg_interactive / total_sum,
        avg_creative_score=avg_creative,
        avg_read_score=avg_read,
        avg_interactive_score=avg_interactive,
        avg_total_score=avg_total,
        avg_articles_per_month=(
            sum(articles_per_month_list) / len(articles_per_month_list)
            if articles_per_month_list
            else 0
        ),
        avg_reads_per_article=(
            sum(reads_per_article_list) / len(reads_per_article_list)
            if reads_per_article_list
            else 0
        ),
        avg_likes_per_article=(
            sum(likes_per_article_list) / len(likes_per_article_list)
            if likes_per_article_list
            else 0
        ),
        avg_favs_per_article=(
            sum(favs_per_article_list) / len(favs_per_article_list)
            if favs_per_article_list
            else 0
        ),
        avg_interactive_rate=(
            sum(interactive_rate_list) / len(interactive_rate_list)
            if interactive_rate_list
            else 0
        ),
        avg_active_month=sum(active_months) / n,
    )


def calculate_frequency_groups(entries: List[RankEntry]) -> List[FrequencyGroup]:
    """按活跃月数分组统计"""
    groups: Dict[int, List[RankEntry]] = {}
    for e in entries:
        month = e.active_month
        if month not in groups:
            groups[month] = []
        groups[month].append(e)

    result = []
    for month in sorted(groups.keys()):
        group = groups[month]
        n = len(group)
        result.append(
            FrequencyGroup(
                active_month=month,
                count=n,
                avg_total_score=sum(e.total_score for e in group) / n,
                avg_creative_score=sum(e.creative_score for e in group) / n,
                avg_read_score=sum(e.read_score for e in group) / n,
                avg_interactive_score=sum(e.interactive_score for e in group) / n,
                avg_article_count=sum(e.article_count for e in group) / n,
            )
        )
    return result


def compare_with_top(
    user_rank: UserRank,
    user_detail: Optional[UserDetail],
    top_entries: List[RankEntry],
    top_details: Optional[Dict[int, UserDetail]] = None,
) -> List[CompetitorInsight]:
    """将用户与 Top 作者对比，生成洞察"""
    if not top_entries:
        return []

    dist = analyze_score_distribution(top_entries)
    total = user_rank.total_score or 1
    user_creative_ratio = user_rank.creative_score / total
    user_read_ratio = user_rank.read_score / total
    user_interactive_ratio = user_rank.interactive_score / total

    insights: List[CompetitorInsight] = []

    # 1. 总热力值
    gap_pct = _calc_gap(user_rank.total_score, dist.avg_total_score)
    insights.append(
        CompetitorInsight(
            dimension="总热力值",
            your_value=f"{user_rank.total_score:.0f}",
            top_avg_value=f"{dist.avg_total_score:.0f}",
            gap=gap_pct,
            suggestion="提升热力值需要同时关注创作分、阅读分和互动分三个维度",
        )
    )

    # 2. 创作分
    gap_pct = _calc_gap(user_rank.creative_score, dist.avg_creative_score)
    insights.append(
        CompetitorInsight(
            dimension="创作分",
            your_value=f"{user_rank.creative_score:.0f} ({user_creative_ratio:.0%})",
            top_avg_value=f"{dist.avg_creative_score:.0f} ({dist.avg_creative_ratio:.0%})",
            gap=gap_pct,
            suggestion="增加原创文章数量，保持每月发文以获得发文系数加成" if gap_pct.startswith("-") else "创作分占比较高，可以适当将精力分配到其他维度",
        )
    )

    # 3. 阅读分
    gap_pct = _calc_gap(user_rank.read_score, dist.avg_read_score)
    insights.append(
        CompetitorInsight(
            dimension="阅读分",
            your_value=f"{user_rank.read_score:.0f} ({user_read_ratio:.0%})",
            top_avg_value=f"{dist.avg_read_score:.0f} ({dist.avg_read_ratio:.0%})",
            gap=gap_pct,
            suggestion="选择热门技术选题，优化标题和封面，利用自荐功能上首页" if gap_pct.startswith("-") else "阅读表现良好，继续保持",
        )
    )

    # 4. 互动分
    gap_pct = _calc_gap(user_rank.interactive_score, dist.avg_interactive_score)
    insights.append(
        CompetitorInsight(
            dimension="互动分",
            your_value=f"{user_rank.interactive_score:.0f} ({user_interactive_ratio:.0%})",
            top_avg_value=f"{dist.avg_interactive_score:.0f} ({dist.avg_interactive_ratio:.0%})",
            gap=gap_pct,
            suggestion="文末添加互动引导（问题、投票），提升内容实用性和可操作性" if gap_pct.startswith("-") else "互动表现良好",
        )
    )

    # 5. 文章数量
    gap_pct = _calc_gap(user_rank.article_count, sum(e.article_count for e in top_entries) / len(top_entries))
    insights.append(
        CompetitorInsight(
            dimension="年度文章数",
            your_value=str(user_rank.article_count),
            top_avg_value=f"{sum(e.article_count for e in top_entries) / len(top_entries):.0f}",
            gap=gap_pct,
            suggestion="保持稳定输出节奏，固定每周发文" if gap_pct.startswith("-") else "文章数量充足",
        )
    )

    # 6. 活跃月数
    gap_pct = _calc_gap(user_rank.active_month, dist.avg_active_month)
    insights.append(
        CompetitorInsight(
            dimension="活跃月数",
            your_value=str(user_rank.active_month),
            top_avg_value=f"{dist.avg_active_month:.1f}",
            gap=gap_pct,
            suggestion="保持每月至少发文1篇，连续活跃可获得发文系数加成" if gap_pct.startswith("-") else "活跃度良好",
        )
    )

    # 7. 单篇阅读量
    user_reads_per_article = (
        user_rank.read_num / user_rank.article_count if user_rank.article_count > 0 else 0
    )
    gap_pct = _calc_gap(user_reads_per_article, dist.avg_reads_per_article)
    insights.append(
        CompetitorInsight(
            dimension="单篇阅读量",
            your_value=f"{user_reads_per_article:.0f}",
            top_avg_value=f"{dist.avg_reads_per_article:.0f}",
            gap=gap_pct,
            suggestion="优化选题和标题，提高文章可读性和实用性" if gap_pct.startswith("-") else "单篇阅读表现优异",
        )
    )

    # 8. 互动率
    user_interactive_rate = (
        (user_rank.like_num + user_rank.fav_num) / user_rank.read_num
        if user_rank.read_num > 0
        else 0
    )
    gap_pct = _calc_gap(user_interactive_rate, dist.avg_interactive_rate)
    insights.append(
        CompetitorInsight(
            dimension="互动率",
            your_value=f"{user_interactive_rate:.1%}",
            top_avg_value=f"{dist.avg_interactive_rate:.1%}",
            gap=gap_pct,
            suggestion="增加实操案例和代码示例，让读者更愿意点赞收藏" if gap_pct.startswith("-") else "互动率表现优秀",
        )
    )

    return insights


def identify_differentiators(entries: List[RankEntry]) -> List[dict]:
    """对比 TOP10 和中间段（20-50名）的差异"""
    if len(entries) < 20:
        return []

    top10 = entries[:10]
    mid = entries[19:50]  # 20-50名

    def avg(lst: List[float]) -> float:
        return sum(lst) / len(lst) if lst else 0

    def compare_dim(
        name: str, top_vals: List[float], mid_vals: List[float], unit: str = ""
    ) -> dict:
        top_avg = avg(top_vals)
        mid_avg = avg(mid_vals)
        diff_pct = ((top_avg - mid_avg) / mid_avg * 100) if mid_avg > 0 else 0
        return {
            "dimension": name,
            "top10_avg": f"{top_avg:.1f}{unit}",
            "rank20_50_avg": f"{mid_avg:.1f}{unit}",
            "difference": f"+{diff_pct:.0f}%" if diff_pct > 0 else f"{diff_pct:.0f}%",
            "insight": _generate_differentiator_insight(name, top_avg, mid_avg, diff_pct),
        }

    results = [
        compare_dim(
            "发文频率(篇/月)",
            [e.article_count / max(e.active_month, 1) for e in top10],
            [e.article_count / max(e.active_month, 1) for e in mid],
            "篇/月",
        ),
        compare_dim(
            "单篇阅读量",
            [e.read_num / max(e.article_count, 1) for e in top10],
            [e.read_num / max(e.article_count, 1) for e in mid],
        ),
        compare_dim(
            "互动率",
            [
                (e.like_num + e.fav_num) / max(e.read_num, 1) * 100
                for e in top10
            ],
            [
                (e.like_num + e.fav_num) / max(e.read_num, 1) * 100
                for e in mid
            ],
            "%",
        ),
        compare_dim(
            "收藏率",
            [e.fav_num / max(e.read_num, 1) * 100 for e in top10],
            [e.fav_num / max(e.read_num, 1) * 100 for e in mid],
            "%",
        ),
        compare_dim(
            "活跃月数",
            [float(e.active_month) for e in top10],
            [float(e.active_month) for e in mid],
            "月",
        ),
    ]

    return results


def generate_action_plan(
    insights: List[CompetitorInsight],
    user_rank: UserRank,
    distribution: ScoreDistribution,
) -> List[ActionItem]:
    """根据洞察生成优先行动计划"""
    actions: List[ActionItem] = []
    priority = 1

    # 找出差距最大的维度
    gaps = []
    for insight in insights:
        if insight.gap.startswith("-"):
            try:
                gap_val = float(insight.gap.replace("%", "").replace("+", ""))
                gaps.append((insight.dimension, gap_val, insight))
            except ValueError:
                pass

    # 按差距从大到小排序
    gaps.sort(key=lambda x: x[1])

    # 1. 活跃月数（如果不足）
    active_insight = next((i for i in insights if i.dimension == "活跃月数"), None)
    if active_insight and active_insight.gap.startswith("-"):
        actions.append(
            ActionItem(
                priority=priority,
                title="提升活跃月数",
                current=f"{user_rank.active_month} 月",
                target=f"{int(distribution.avg_active_month)}+ 月",
                expected_impact="所有分值乘数提升，是最基础的加分项",
                action="确保每月至少发文1篇，保持连续活跃获得发文系数加成",
            )
        )
        priority += 1

    # 2. 发文频率
    article_insight = next((i for i in insights if i.dimension == "年度文章数"), None)
    if article_insight and article_insight.gap.startswith("-"):
        target_articles = int(distribution.avg_articles_per_month * 12)
        actions.append(
            ActionItem(
                priority=priority,
                title="提升发文频率",
                current=f"{user_rank.article_count} 篇/年",
                target=f"{target_articles}+ 篇/年",
                expected_impact=f"预计创作分可提升 {abs(float(article_insight.gap.replace('%',''))):.0f}%",
                action=f"每周固定发文1篇，建立写作节奏，月均{distribution.avg_articles_per_month:.1f}篇对标TOP作者",
            )
        )
        priority += 1

    # 3. 互动率
    interactive_insight = next((i for i in insights if i.dimension == "互动率"), None)
    if interactive_insight and interactive_insight.gap.startswith("-"):
        actions.append(
            ActionItem(
                priority=priority,
                title="提升互动率",
                current=interactive_insight.your_value,
                target=f"{distribution.avg_interactive_rate:.1%}+",
                expected_impact="互动分提升，读者粘性增强",
                action="文末添加问题引导、投票互动，增加实操案例让读者更愿意收藏",
            )
        )
        priority += 1

    # 4. 单篇阅读量
    reads_insight = next((i for i in insights if i.dimension == "单篇阅读量"), None)
    if reads_insight and reads_insight.gap.startswith("-"):
        actions.append(
            ActionItem(
                priority=priority,
                title="提升单篇阅读量",
                current=reads_insight.your_value,
                target=f"{distribution.avg_reads_per_article:.0f}+",
                expected_impact="阅读分显著提升",
                action="优化标题吸引力，选择热门选题，文章发布7天内使用自荐功能上首页",
            )
        )
        priority += 1

    # 5. 如果互动分差距最大
    score_gaps = [
        ("创作分", user_rank.creative_score, distribution.avg_creative_score),
        ("阅读分", user_rank.read_score, distribution.avg_read_score),
        ("互动分", user_rank.interactive_score, distribution.avg_interactive_score),
    ]
    biggest_gap = min(score_gaps, key=lambda x: x[1] / max(x[2], 1))
    if biggest_gap[1] < biggest_gap[2]:
        dim_name, your_val, top_val = biggest_gap
        gap_pct = (1 - your_val / top_val) * 100 if top_val > 0 else 0
        actions.append(
            ActionItem(
                priority=priority,
                title=f"重点提升{dim_name}（差距最大）",
                current=f"{your_val:.0f}",
                target=f"{top_val:.0f}",
                expected_impact=f"当前{dim_name}仅达TOP作者的{100-gap_pct:.0f}%，提升空间最大",
                action=_score_gap_action(dim_name),
            )
        )
        priority += 1

    return actions


def _calc_gap(your_value: float, top_avg: float) -> str:
    """计算差距百分比，返回格式如 '+15%' 或 '-40%'"""
    if top_avg == 0:
        return "+0%" if your_value >= 0 else "-0%"
    pct = (your_value - top_avg) / top_avg * 100
    if pct >= 0:
        return f"+{pct:.0f}%"
    else:
        return f"{pct:.0f}%"


def _generate_differentiator_insight(
    name: str, top_avg: float, mid_avg: float, diff_pct: float
) -> str:
    """生成差异洞察描述"""
    insights = {
        "发文频率(篇/月)": f"TOP10作者平均每月发文{top_avg:.1f}篇，是中间段作者的{top_avg/mid_avg:.1f}倍。保持稳定的发文节奏是进入前十的关键",
        "单篇阅读量": f"TOP10作者单篇平均阅读{top_avg:.0f}次，内容质量更高、选题更精准。优化选题角度和标题是提升阅读的核心",
        "互动率": f"TOP10互动率{top_avg:.1f}%，说明内容更具实用性和参考价值，读者更愿意点赞收藏",
        "收藏率": f"TOP10收藏率{top_avg:.1f}%，收藏率高说明文章具有长期参考价值，读者会反复查看",
        "活跃月数": f"TOP10平均活跃{top_avg:.0f}个月，保持长期稳定的输出节奏是基础",
    }
    return insights.get(name, f"TOP10此维度均值{top_avg:.1f}，中间段{mid_avg:.1f}，差距{diff_pct:+.0f}%")


def _score_gap_action(dim_name: str) -> str:
    """生成分值差距的行动建议"""
    actions = {
        "创作分": "增加原创文章产出，保持每月稳定发文以获取发文系数加成",
        "阅读分": "优化标题和选题，选择当下热门技术方向，利用自荐上首页增加曝光",
        "互动分": "增加代码示例和实操步骤，文末设置互动引导，提升内容收藏价值",
    }
    return actions.get(dim_name, "全面提升内容质量和产出频率")
