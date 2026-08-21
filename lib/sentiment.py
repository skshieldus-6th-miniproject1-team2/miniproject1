"""7종 감정 → 긍정/중립/부정 3그룹 매핑. README.md '감정 3그룹 매핑 (확정)' 절 그대로.

모델: dlckdfuf141/korean-emotion-kluebert-v2 (7종 감정)
긍정 = 행복
중립 = 중립 · 놀람   (놀람은 중립으로 묶는다 — 고정, 바꾸지 말 것)
부정 = 혐오 · 분노 · 슬픔 · 공포
"""
from __future__ import annotations

import pandas as pd

EMOTIONS_7 = ["행복", "중립", "놀람", "혐오", "분노", "슬픔", "공포"]

GROUP_MAP = {
    "행복": "긍정",
    "중립": "중립",
    "놀람": "중립",
    "혐오": "부정",
    "분노": "부정",
    "슬픔": "부정",
    "공포": "부정",
}

GROUP_ORDER = ["긍정", "중립", "부정"]


def to_group(emotion: str) -> str:
    return GROUP_MAP.get(emotion, "중립")


def add_group_column(df: pd.DataFrame, emotion_col: str = "감정", out_col: str = "감정그룹") -> pd.DataFrame:
    df = df.copy()
    df[out_col] = df[emotion_col].map(GROUP_MAP).fillna("중립")
    return df


def group_ratio(df: pd.DataFrame, emotion_col: str = "감정", by: list[str] | None = None) -> pd.DataFrame:
    """감정그룹별 건수·비율. by를 주면 (예: ['정책']) 그룹별로 100% 기준 비율을 낸다."""
    tagged = add_group_column(df, emotion_col)
    group_cols = (by or []) + ["감정그룹"]
    counts = tagged.groupby(group_cols).size().reset_index(name="건수")
    totals = counts.groupby(by)["건수"].transform("sum") if by else counts["건수"].sum()
    counts["비율"] = counts["건수"] / totals
    return counts
