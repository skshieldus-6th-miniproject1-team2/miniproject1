"""뉴스 감정 3그룹(긍정/중립/부정) 관련 헬퍼.

News_Scraping.csv의 '감정' 컬럼은 이미 긍정/중립/부정 3그룹으로 분류돼 있어
별도 매핑 없이 그대로 쓴다.
"""
from __future__ import annotations

import pandas as pd

GROUP_ORDER = ["긍정", "중립", "부정"]


def add_group_column(df: pd.DataFrame, emotion_col: str = "감정", out_col: str = "감정그룹") -> pd.DataFrame:
    df = df.copy()
    df[out_col] = df[emotion_col]
    return df


def group_ratio(df: pd.DataFrame, emotion_col: str = "감정", by: list[str] | None = None) -> pd.DataFrame:
    """감정그룹별 건수·비율. by를 주면 (예: ['정책']) 그룹별로 100% 기준 비율을 낸다."""
    tagged = add_group_column(df, emotion_col)
    group_cols = (by or []) + ["감정그룹"]
    counts = tagged.groupby(group_cols).size().reset_index(name="건수")
    totals = counts.groupby(by)["건수"].transform("sum") if by else counts["건수"].sum()
    counts["비율"] = counts["건수"] / totals
    return counts
