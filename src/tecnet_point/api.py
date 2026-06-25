"""腾讯云开发者社区 API 客户端"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

import requests

from .models import (
    RankEntry,
    UserInfo,
    UserDetail,
    UserRank,
    ValuableAuthor,
)

logger = logging.getLogger(__name__)


class TencentDevClient:
    """腾讯云开发者社区 API 客户端"""

    BASE_URL = "https://cloud.tencent.com/developer/api"

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        page_delay: float = 1.0,
    ):
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cloud.tencent.com/developer/rank",
            }
        )
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._page_delay = page_delay

    def _request(self, endpoint: str, data: dict) -> Optional[dict]:
        """发送 POST 请求，带重试逻辑"""
        url = f"{self.BASE_URL}/{endpoint}"
        for attempt in range(self._max_retries):
            try:
                resp = self._session.post(url, json=data, timeout=self._timeout)
                resp.raise_for_status()
                result = resp.json()
                if result.get("code") and result.get("code") != 0:
                    logger.warning("API error for %s: %s", endpoint, result.get("msg"))
                    return None
                return result
            except requests.exceptions.RequestException as e:
                logger.warning(
                    "Request failed for %s (attempt %d/%d): %s",
                    endpoint,
                    attempt + 1,
                    self._max_retries,
                    e,
                )
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay * (2**attempt))
        return None

    @staticmethod
    def _parse_user_info(data: dict) -> UserInfo:
        """解析用户信息"""
        return UserInfo(
            uid=data.get("uid", 0),
            nickname=data.get("nickname", ""),
            avatar=data.get("avatarUrl", ""),
            level=data.get("level", 0),
            growth=data.get("growth", 0),
            privilege=data.get("privilege", 0),
            company=data.get("company", ""),
            title=data.get("title", ""),
            introduce=data.get("introduce", ""),
            article_num=data.get("articleNum", 0),
            article_read_num=data.get("articleReadNum", 0),
            article_fav_num=data.get("articleFavNum", 0),
            be_concern_user_num=data.get("beConcernUserNum", 0),
            medals=data.get("medals", data.get("userMedals", [])),
        )

    def _parse_rank_entry(self, data: dict) -> RankEntry:
        """解析热力值排行条目"""
        user_data = data.get("user", {})
        # yesterdayRank might be in data or user
        yesterday_rank = data.get("yesterdayRank") or data.get("lastRank")
        return RankEntry(
            rank=data.get("rank", 0),
            user=self._parse_user_info(user_data),
            total_score=data.get("totalScore", 0),
            creative_score=data.get("creativeScore", 0),
            read_score=data.get("readScore", 0),
            interactive_score=data.get("interactiveScore", 0),
            article_count=data.get("articleCount", 0),
            active_month=data.get("activeMonth", 0),
            cur_month_article_count=data.get("curMonthArticleCount", 0),
            read_num=data.get("readNum", 0),
            like_num=data.get("likeNum", 0),
            fav_num=data.get("favNum", 0),
            yesterday_rank=yesterday_rank,
        )

    def _parse_valuable_author(self, data: dict) -> ValuableAuthor:
        """解析最具价值作者条目"""
        user_data = data.get("userInfo", data.get("user", {}))
        return ValuableAuthor(
            rank=data.get("rank", 0),
            user=self._parse_user_info(user_data),
            score=data.get("score", 0),
            quality_score=data.get("qualityScore", 0),
            influence_score=data.get("influenceScore", 0),
            activity_score=data.get("activityScore", 0),
            factor=data.get("factor", 1.0),
        )

    # ---- 公开 API 方法 ----

    def fetch_rank_list(
        self, year: int = 2026, page: int = 1, pagesize: int = 10
    ) -> List[RankEntry]:
        """获取热力值排行榜"""
        data = self._request("rank/list", {"year": year, "pagesize": pagesize, "page": page})
        if not data:
            return []
        items = data.get("list", [])
        return [self._parse_rank_entry(item) for item in items]

    def fetch_all_rank_list(
        self, year: int = 2026, max_entries: int = 100
    ) -> List[RankEntry]:
        """获取热力值排行榜（自动分页）"""
        all_entries: List[RankEntry] = []
        page = 1
        pagesize = 10
        while len(all_entries) < max_entries:
            entries = self.fetch_rank_list(year, page, pagesize)
            if not entries:
                break
            all_entries.extend(entries)
            if len(entries) < pagesize:
                break
            page += 1
            time.sleep(self._page_delay)
        return all_entries[:max_entries]

    def fetch_valuable_list(
        self, year: int = 2026, page: int = 1, pagesize: int = 10
    ) -> tuple[List[ValuableAuthor], int]:
        """获取最具价值作者排行榜，返回 (列表, 总数)"""
        data = self._request(
            "rank/most-valuable-list",
            {"year": year, "pagesize": pagesize, "page": page},
        )
        if not data:
            return [], 0
        items = data.get("list", [])
        total = data.get("total", 0)
        authors = [self._parse_valuable_author(item) for item in items]
        return authors, total

    def fetch_all_valuable_list(
        self, year: int = 2026, max_entries: int = 100
    ) -> List[ValuableAuthor]:
        """获取最具价值作者排行榜（自动分页）"""
        all_authors: List[ValuableAuthor] = []
        page = 1
        pagesize = 10
        while len(all_authors) < max_entries:
            authors, total = self.fetch_valuable_list(year, page, pagesize)
            if not authors:
                break
            all_authors.extend(authors)
            if len(all_authors) >= total or len(authors) < pagesize:
                break
            page += 1
            time.sleep(self._page_delay)
        return all_authors[:max_entries]

    def fetch_user_rank(self, uid: int, year: int = 2026) -> Optional[UserRank]:
        """获取用户排名数据"""
        data = self._request("user/rank", {"uid": uid, "year": year})
        if not data:
            return None
        user_data = data.get("user", {})
        return UserRank(
            rank=data.get("rank", 0),
            user=self._parse_user_info(user_data),
            total_score=data.get("totalScore", 0),
            creative_score=data.get("creativeScore", 0),
            read_score=data.get("readScore", 0),
            interactive_score=data.get("interactiveScore", 0),
            article_count=data.get("articleCount", 0),
            active_month=data.get("activeMonth", 0),
            cur_month_article_count=data.get("curMonthArticleCount", 0),
            read_num=data.get("readNum", 0),
            like_num=data.get("likeNum", 0),
            fav_num=data.get("favNum", 0),
        )

    def fetch_user_detail(self, uid: int) -> Optional[UserDetail]:
        """获取用户详情"""
        data = self._request("user/detail", {"uid": uid})
        if not data:
            return None
        return UserDetail(
            uid=data.get("uid", 0),
            nickname=data.get("nickname", ""),
            avatar=data.get("avatarUrl", ""),
            level=data.get("level", 0),
            growth=data.get("growth", 0),
            privilege=data.get("privilege", 0),
            article_num=data.get("articleNum", 0),
            article_read_num=data.get("articleReadNum", 0),
            article_fav_num=data.get("articleFavNum", 0),
            article_like_num=data.get("articleLikeNum", 0),
            article_comment_num=data.get("articleCommentNum", 0),
            article_recomm_num=data.get("articleRecommNum", 0),
            be_concern_user_num=data.get("beConcernUserNum", 0),
            answer_num=data.get("answerNum", 0),
            ask_num=data.get("askNum", 0),
            company=data.get("company", ""),
            title=data.get("title", ""),
            introduce=data.get("introduce", ""),
            is_original_author=data.get("isOriginalAuthor", 0),
            join_column_num=data.get("joinColumnNum", 0),
        )
