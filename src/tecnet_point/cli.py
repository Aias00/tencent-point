"""CLI 入口"""

from __future__ import annotations

import json
import sys
from datetime import datetime

import click
from rich.console import Console
from rich.panel import Panel

from .api import TencentDevClient
from .competitor_analysis import (
    analyze_score_distribution,
    calculate_frequency_groups,
    compare_with_top,
    generate_action_plan,
    identify_differentiators,
)
from .config import load_config
from .formatter import (
    print_action_plan,
    print_competitor_comparison,
    print_differentiators,
    print_frequency_groups,
    print_rank_table,
    print_score_distribution,
    print_topic_suggestions,
    print_user_card,
    print_valuable_table,
)
from .topic_recommend import (
    analyze_engagement_patterns,
    calculate_optimal_posting_frequency,
    generate_topic_suggestions,
    identify_low_hanging_fruit,
)

console = Console()


def get_client(config: dict) -> TencentDevClient:
    """从配置创建 API 客户端"""
    api_config = config.get("api", {})
    return TencentDevClient(
        timeout=api_config.get("timeout", 30),
        max_retries=api_config.get("max_retries", 3),
        retry_delay=api_config.get("retry_delay", 2.0),
        page_delay=api_config.get("page_delay", 1.0),
    )


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="启用调试日志")
@click.version_option(version="0.1.0", prog_name="tecnet-point")
@click.pass_context
def cli(ctx, verbose):
    """tecnet-point — 腾讯云开发者社区热力值分析工具"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = load_config()


@cli.command()
@click.option("--year", "-y", type=int, default=None, help="排名年份 (默认: 当前年)")
@click.option("--top", "-n", type=int, default=None, help="分析 TOP N 作者 (默认: 50)")
@click.option("--json", "as_json", is_flag=True, help="JSON 格式输出")
@click.pass_context
def topic(ctx, year, top, as_json):
    """选题推荐 — 分析热门趋势，推荐写作选题"""
    config = ctx.obj["config"]
    year = year or config.get("year", datetime.now().year)
    top_n = top or config.get("top_n", 50)
    categories = config.get("categories", [])

    console.print(f"[bold green]📊 正在获取 {year} 年热力值排行 TOP{top_n} 数据...[/bold green]")
    client = get_client(config)
    entries = client.fetch_all_rank_list(year, max_entries=top_n)

    if not entries:
        console.print("[bold red]❌ 获取排行数据失败，请检查网络连接[/bold red]")
        sys.exit(1)

    console.print(f"[green]✓ 获取到 {len(entries)} 位作者数据[/green green]")

    # 分析
    dist = analyze_score_distribution(entries)
    engagement = analyze_engagement_patterns(entries)
    freq = calculate_optimal_posting_frequency(entries)

    # 获取用户数据（如果配置了 uid）
    user_rank = None
    user_detail = None
    uid = config.get("uid", 0)
    if uid:
        console.print(f"[dim]正在获取您的排名数据 (uid: {uid})...[/dim]")
        user_rank = client.fetch_user_rank(uid, year)
        user_detail = client.fetch_user_detail(uid)

    # 生成推荐
    fruits = identify_low_hanging_fruit(user_rank, dist, engagement)
    suggestions = generate_topic_suggestions(dist, categories, user_rank, user_detail, entries)

    if as_json:
        output = {
            "year": year,
            "top_n_analyzed": len(entries),
            "score_distribution": {
                "avg_creative_ratio": dist.avg_creative_ratio,
                "avg_read_ratio": dist.avg_read_ratio,
                "avg_interactive_ratio": dist.avg_interactive_ratio,
                "avg_total_score": dist.avg_total_score,
            },
            "engagement_patterns": engagement,
            "posting_frequency": {
                "recommendation": freq.get("recommendation", ""),
                "best_active_month": freq.get("best_active_month", 0),
            },
            "low_hanging_fruit": fruits,
            "suggestions": [
                {
                    "topic": s.topic,
                    "angle": s.angle,
                    "rationale": s.rationale,
                    "expected_impact": s.expected_impact,
                    "difficulty": s.difficulty,
                    "reference_authors": s.reference_authors,
                }
                for s in suggestions
            ],
        }
        if user_rank:
            output["user_rank"] = {
                "rank": user_rank.rank,
                "total_score": user_rank.total_score,
                "creative_score": user_rank.creative_score,
                "read_score": user_rank.read_score,
                "interactive_score": user_rank.interactive_score,
            }
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # Rich 输出
    console.print()
    print_score_distribution(dist, console)

    # 发文频率分析
    freq_groups = freq.get("frequency_groups", [])
    if freq_groups:
        print_frequency_groups(freq_groups, console)
    console.print(f"[bold]💡 {freq.get('recommendation', '')}[/bold]")

    # 最低成本提升方向
    if fruits:
        console.print()
        console.print(Panel("🍎 最低成本提升方向", style="bold yellow", border_style="yellow"))
        for fruit in fruits:
            console.print(f"  • {fruit}")

    # 用户数据卡片
    if user_rank:
        console.print()
        print_user_card(user_rank, user_detail, console)

    # 选题推荐
    print_topic_suggestions(suggestions, console)


@cli.command()
@click.option("--year", "-y", type=int, default=None, help="排名年份 (默认: 当前年)")
@click.option("--top", "-n", type=int, default=None, help="对比 TOP N 作者 (默认: 50)")
@click.option("--json", "as_json", is_flag=True, help="JSON 格式输出")
@click.pass_context
def competitor(ctx, year, top, as_json):
    """竞品分析 — 对比 TOP 作者，找出差距和提升方向"""
    config = ctx.obj["config"]
    year = year or config.get("year", datetime.now().year)
    top_n = top or config.get("top_n", 50)
    uid = config.get("uid", 0)

    if not uid:
        console.print(
            "[bold yellow]⚠️  未配置 uid，将以匿名模式运行（仅展示 TOP 作者分析）[/bold yellow]"
        )
        console.print("[dim]在 config.yaml 中设置 uid 以获取个人对比数据[/dim]")

    console.print(f"[bold green]📊 正在获取 {year} 年热力值排行 TOP{top_n} 数据...[/bold green]")
    client = get_client(config)
    entries = client.fetch_all_rank_list(year, max_entries=top_n)

    if not entries:
        console.print("[bold red]❌ 获取排行数据失败，请检查网络连接[/bold red]")
        sys.exit(1)

    console.print(f"[green]✓ 获取到 {len(entries)} 位作者数据[/green]")

    # 分析
    dist = analyze_score_distribution(entries)
    differentiators = identify_differentiators(entries)

    # 获取用户数据
    user_rank = None
    user_detail = None
    insights = []
    actions = []

    if uid:
        console.print(f"[dim]正在获取您的排名数据 (uid: {uid})...[/dim]")
        user_rank = client.fetch_user_rank(uid, year)
        user_detail = client.fetch_user_detail(uid)

        if user_rank:
            insights = compare_with_top(user_rank, user_detail, entries)
            actions = generate_action_plan(insights, user_rank, dist)

    if as_json:
        output = {
            "year": year,
            "top_n_analyzed": len(entries),
            "score_distribution": {
                "avg_creative_ratio": dist.avg_creative_ratio,
                "avg_read_ratio": dist.avg_read_ratio,
                "avg_interactive_ratio": dist.avg_interactive_ratio,
                "avg_total_score": dist.avg_total_score,
                "avg_articles_per_month": dist.avg_articles_per_month,
                "avg_reads_per_article": dist.avg_reads_per_article,
                "avg_interactive_rate": dist.avg_interactive_rate,
            },
            "differentiators": differentiators,
        }
        if user_rank:
            output["user"] = {
                "rank": user_rank.rank,
                "total_score": user_rank.total_score,
                "creative_score": user_rank.creative_score,
                "read_score": user_rank.read_score,
                "interactive_score": user_rank.interactive_score,
                "article_count": user_rank.article_count,
                "active_month": user_rank.active_month,
            }
            output["insights"] = [
                {
                    "dimension": i.dimension,
                    "your_value": i.your_value,
                    "top_avg_value": i.top_avg_value,
                    "gap": i.gap,
                    "suggestion": i.suggestion,
                }
                for i in insights
            ]
            output["action_plan"] = [
                {
                    "priority": a.priority,
                    "title": a.title,
                    "current": a.current,
                    "target": a.target,
                    "expected_impact": a.expected_impact,
                    "action": a.action,
                }
                for a in actions
            ]
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # Rich 输出
    console.print()
    print_score_distribution(dist, console)

    # TOP10 vs 中间段差异
    if differentiators:
        print_differentiators(differentiators, console)

    # 用户对比
    if user_rank:
        console.print()
        print_user_card(user_rank, user_detail, console)

        if insights:
            print_competitor_comparison(insights, console)

        if actions:
            print_action_plan(actions, console)
    else:
        console.print()
        console.print(
            Panel(
                "💡 在 config.yaml 中设置 uid 后，可获取个人对比数据和行动计划\n"
                "示例: uid: 12345678",
                title="提示",
                border_style="yellow",
            )
        )


@cli.command()
@click.option("--type", "rank_type", type=click.Choice(["heat", "valuable"]), default="heat")
@click.option("--year", "-y", type=int, default=None, help="排名年份")
@click.option("--page", "-p", type=int, default=1, help="页码")
@click.option("--pagesize", "-s", type=int, default=20, help="每页数量")
@click.pass_context
def rank(ctx, rank_type, year, page, pagesize):
    """查看排名 — 热力值排名或最具价值作者排名"""
    config = ctx.obj["config"]
    year = year or config.get("year", datetime.now().year)
    client = get_client(config)

    if rank_type == "heat":
        console.print(f"[bold green]📊 正在获取 {year} 年热力值排行...[/bold green]")
        entries = client.fetch_rank_list(year, page, pagesize)
        if entries:
            print_rank_table(entries, console, title=f"🔥 热力值排行 {year}年 (第{page}页)")
        else:
            console.print("[bold red]❌ 获取排行数据失败[/bold red]")
    else:
        console.print(f"[bold green]🏆 正在获取 {year} 年最具价值作者排行...[/bold green]")
        authors, total = client.fetch_valuable_list(year, page, pagesize)
        if authors:
            print_valuable_table(
                authors, console, title=f"🏆 最具价值作者榜 {year}年 (第{page}页, 共{total}人)"
            )
        else:
            console.print("[bold red]❌ 获取排行数据失败[/bold red]")


@cli.command()
@click.option("--uid", type=int, required=True, help="用户 UID")
@click.option("--year", "-y", type=int, default=None, help="排名年份")
@click.pass_context
def me(ctx, uid, year):
    """查看我的数据 — 查看指定用户的热力值和详情"""
    config = ctx.obj["config"]
    year = year or config.get("year", datetime.now().year)
    client = get_client(config)

    console.print(f"[bold green]📊 正在获取用户数据 (uid: {uid})...[/bold green]")

    user_rank = client.fetch_user_rank(uid, year)
    user_detail = client.fetch_user_detail(uid)

    if not user_rank and not user_detail:
        console.print(f"[bold red]❌ 未找到用户数据 (uid: {uid})，请确认 UID 是否正确[/bold red]")
        sys.exit(1)

    if user_rank:
        print_user_card(user_rank, user_detail, console)
    elif user_detail:
        # 仅有详情无排名数据
        content = f"👤 {user_detail.nickname}  Lv{user_detail.level}  成长值 {user_detail.growth}\n\n"
        content += f"📚 总文章数: {user_detail.article_num}\n"
        content += f"📖 总阅读量: {user_detail.article_read_num:,}\n"
        content += f"⭐ 总收藏数: {user_detail.article_fav_num:,}\n"
        content += f"👥 粉丝数: {user_detail.be_concern_user_num}\n"
        if user_rank is None:
            content += "\n⚠️ 未上榜（年度需发布2篇以上原创文章）"
        console.print(Panel(content, title="用户数据", border_style="blue"))


if __name__ == "__main__":
    cli()
