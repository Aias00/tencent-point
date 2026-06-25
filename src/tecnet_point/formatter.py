"""Rich 终端输出格式化"""

from __future__ import annotations

from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import (
    ActionItem,
    CompetitorInsight,
    FrequencyGroup,
    RankEntry,
    ScoreDistribution,
    TopicSuggestion,
    UserDetail,
    UserRank,
    ValuableAuthor,
)


def print_rank_table(
    entries: List[RankEntry], console: Console, title: str = "🔥 热力值排行榜"
) -> None:
    """打印热力值排行表格"""
    table = Table(title=title, show_lines=True, padding=(0, 1))
    table.add_column("排名", style="bold cyan", width=6, justify="center")
    table.add_column("昵称", style="bold", width=18)
    table.add_column("等级", width=6, justify="center")
    table.add_column("热力值", style="bold yellow", width=10, justify="right")
    table.add_column("创作分", width=8, justify="right")
    table.add_column("阅读分", width=8, justify="right")
    table.add_column("互动分", width=8, justify="right")
    table.add_column("文章数", width=6, justify="right")
    table.add_column("活跃月", width=6, justify="center")

    for e in entries[:50]:
        rank_style = ""
        if e.rank == 1:
            rank_style = "bold gold1"
        elif e.rank == 2:
            rank_style = "bold silver"
        elif e.rank == 3:
            rank_style = "bold orange3"

        rank_text = Text(str(e.rank), style=rank_style) if rank_style else str(e.rank)
        table.add_row(
            rank_text,
            e.user.nickname[:18],
            f"Lv{e.user.level}",
            f"{e.total_score:.0f}",
            f"{e.creative_score:.0f}",
            f"{e.read_score:.0f}",
            f"{e.interactive_score:.0f}",
            str(e.article_count),
            str(e.active_month),
        )

    console.print(table)


def print_valuable_table(
    authors: List[ValuableAuthor],
    console: Console,
    title: str = "🏆 最具价值作者榜",
) -> None:
    """打印最具价值作者排行表格"""
    table = Table(title=title, show_lines=True, padding=(0, 1))
    table.add_column("排名", style="bold cyan", width=6, justify="center")
    table.add_column("昵称", style="bold", width=18)
    table.add_column("贡献值", style="bold yellow", width=10, justify="right")
    table.add_column("质量贡献", width=8, justify="right")
    table.add_column("影响力贡献", width=10, justify="right")
    table.add_column("活动贡献", width=8, justify="right")
    table.add_column("加成系数", width=8, justify="center")

    for a in authors[:50]:
        rank_style = ""
        if a.rank == 1:
            rank_style = "bold gold1"
        elif a.rank == 2:
            rank_style = "bold silver"
        elif a.rank == 3:
            rank_style = "bold orange3"

        rank_text = Text(str(a.rank), style=rank_style) if rank_style else str(a.rank)
        table.add_row(
            rank_text,
            a.user.nickname[:18],
            f"{a.score:.1f}",
            f"{a.quality_score:.1f}",
            f"{a.influence_score:.1f}",
            f"{a.activity_score:.1f}",
            f"×{a.factor:.1f}",
        )

    console.print(table)


def print_user_card(
    user_rank: UserRank,
    user_detail: Optional[UserDetail],
    console: Console,
) -> None:
    """打印用户数据卡片"""
    nickname = user_rank.user.nickname or (user_detail.nickname if user_detail else "未知")
    level = user_rank.user.level or (user_detail.level if user_detail else 0)
    growth = user_rank.user.growth or (user_detail.growth if user_detail else 0)

    content = Text()
    content.append(f"👤 {nickname}", style="bold")
    content.append(f"  Lv{level}  成长值 {growth}\n\n")

    if user_rank.rank > 0:
        content.append(f"📊 排名: #{user_rank.rank}\n", style="bold yellow")
    content.append(f"🔥 热力值: {user_rank.total_score:.0f}\n\n")

    # 分值构成
    total = user_rank.total_score or 1
    creative_pct = user_rank.creative_score / total * 100
    read_pct = user_rank.read_score / total * 100
    interact_pct = user_rank.interactive_score / total * 100

    content.append("📈 分值构成:\n")
    content.append(f"  创作分: {user_rank.creative_score:.0f} ({creative_pct:.1f}%)\n")
    content.append(f"  阅读分: {user_rank.read_score:.0f} ({read_pct:.1f}%)\n")
    content.append(f"  互动分: {user_rank.interactive_score:.0f} ({interact_pct:.1f}%)\n\n")

    content.append("📝 文章数据:\n")
    content.append(f"  年度文章数: {user_rank.article_count}\n")
    content.append(f"  活跃月数: {user_rank.active_month}\n")
    content.append(f"  当月发文: {user_rank.cur_month_article_count} 篇\n")
    content.append(f"  阅读量: {user_rank.read_num:,}\n")
    content.append(f"  点赞数: {user_rank.like_num:,}\n")
    content.append(f"  收藏数: {user_rank.fav_num:,}\n")

    if user_detail:
        content.append(f"\n📚 累计数据:\n")
        content.append(f"  总文章数: {user_detail.article_num}\n")
        content.append(f"  总阅读量: {user_detail.article_read_num:,}\n")
        content.append(f"  总收藏数: {user_detail.article_fav_num:,}\n")
        content.append(f"  粉丝数: {user_detail.be_concern_user_num}\n")

    console.print(Panel(content, title="我的数据", border_style="blue"))


def print_score_distribution(dist: ScoreDistribution, console: Console) -> None:
    """打印分值构成分析"""
    table = Table(title="📊 TOP 作者平均分值构成", show_lines=True, padding=(0, 1))
    table.add_column("分值维度", style="bold", width=12)
    table.add_column("平均占比", width=10, justify="right")
    table.add_column("平均分值", width=10, justify="right")

    table.add_row("创作分", f"{dist.avg_creative_ratio:.1%}", f"{dist.avg_creative_score:.0f}")
    table.add_row("阅读分", f"{dist.avg_read_ratio:.1%}", f"{dist.avg_read_score:.0f}")
    table.add_row("互动分", f"{dist.avg_interactive_ratio:.1%}", f"{dist.avg_interactive_score:.0f}")
    table.add_row(
        "[bold]合计[/bold]",
        "[bold]100%[/bold]",
        f"[bold]{dist.avg_total_score:.0f}[/bold]",
    )

    console.print(table)

    # 关键指标
    metrics = Table(title="🎯 关键指标", show_lines=True, padding=(0, 1))
    metrics.add_column("指标", style="bold", width=16)
    metrics.add_column("TOP 作者平均", width=14, justify="right")

    metrics.add_row("月均发文", f"{dist.avg_articles_per_month:.1f} 篇")
    metrics.add_row("单篇阅读量", f"{dist.avg_reads_per_article:.0f}")
    metrics.add_row("单篇点赞数", f"{dist.avg_likes_per_article:.0f}")
    metrics.add_row("单篇收藏数", f"{dist.avg_favs_per_article:.0f}")
    metrics.add_row("互动率", f"{dist.avg_interactive_rate:.1%}")
    metrics.add_row("平均活跃月数", f"{dist.avg_active_month:.1f}")

    console.print(metrics)


def print_frequency_groups(groups: List[FrequencyGroup], console: Console) -> None:
    """打印活跃月数分组统计"""
    table = Table(title="📅 活跃月数与热力值关系", show_lines=True, padding=(0, 1))
    table.add_column("活跃月数", style="bold", width=10, justify="center")
    table.add_column("人数", width=6, justify="right")
    table.add_column("平均热力值", style="yellow", width=12, justify="right")
    table.add_column("平均创作分", width=10, justify="right")
    table.add_column("平均阅读分", width=10, justify="right")
    table.add_column("平均互动分", width=10, justify="right")

    for g in sorted(groups, key=lambda x: x.active_month):
        table.add_row(
            str(g.active_month),
            str(g.count),
            f"{g.avg_total_score:.0f}",
            f"{g.avg_creative_score:.0f}",
            f"{g.avg_read_score:.0f}",
            f"{g.avg_interactive_score:.0f}",
        )

    console.print(table)


def print_topic_suggestions(
    suggestions: List[TopicSuggestion], console: Console
) -> None:
    """打印选题推荐"""
    console.print()
    console.print(Panel("💡 选题推荐", style="bold green", border_style="green"))

    for i, s in enumerate(suggestions, 1):
        difficulty_color = {
            "简单": "green",
            "中等": "yellow",
            "困难": "red",
        }.get(s.difficulty, "white")

        content = Text()
        content.append(f"📌 {s.topic}\n", style="bold")
        content.append(f"   角度: {s.angle}\n")
        content.append(f"   理由: {s.rationale}\n")
        content.append(f"   预期收益: {s.expected_impact}\n")
        content.append(f"   难度: ", style="dim")
        content.append(s.difficulty, style=difficulty_color)
        if s.reference_authors:
            content.append(f"\n   参考: {', '.join(s.reference_authors)}", style="dim")

        console.print(Panel(content, title=f"#{i}", border_style="dim"))


def print_competitor_comparison(
    insights: List[CompetitorInsight], console: Console
) -> None:
    """打印竞品对比"""
    table = Table(
        title="📊 您与 TOP 作者的差距对比", show_lines=True, padding=(0, 1)
    )
    table.add_column("维度", style="bold", width=14)
    table.add_column("您", width=12, justify="right")
    table.add_column("TOP平均", width=12, justify="right")
    table.add_column("差距", width=10, justify="right")
    table.add_column("建议", width=30)

    for insight in insights:
        gap_style = "red" if insight.gap.startswith("-") else "green"
        table.add_row(
            insight.dimension,
            insight.your_value,
            insight.top_avg_value,
            Text(insight.gap, style=gap_style),
            insight.suggestion,
        )

    console.print(table)


def print_differentiators(differentiators: List[dict], console: Console) -> None:
    """打印 TOP10 vs 中间段差异分析"""
    console.print()
    console.print(
        Panel("🔍 TOP10 vs 中间段差异分析", style="bold magenta", border_style="magenta")
    )

    for d in differentiators:
        content = Text()
        content.append(f"{d['dimension']}: ", style="bold")
        content.append(f"TOP10 平均 {d['top10_avg']}", style="cyan")
        content.append(f"  vs  中间段平均 {d['rank20_50_avg']}", style="dim")
        content.append(f"  ({d['difference']})", style="bold yellow")
        content.append(f"\n💡 {d['insight']}")
        console.print(Panel(content, border_style="dim"))


def print_action_plan(actions: List[ActionItem], console: Console) -> None:
    """打印行动计划"""
    console.print()
    console.print(Panel("📋 优先行动计划", style="bold cyan", border_style="cyan"))

    for a in actions:
        content = Text()
        content.append(f"🎯 {a.title}\n", style="bold")
        content.append(f"   当前: {a.current} → 目标: {a.target}\n")
        content.append(f"   预期效果: {a.expected_impact}\n")
        content.append(f"   行动: {a.action}")

        console.print(Panel(content, title=f"#{a.priority}", border_style="blue"))
