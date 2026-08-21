"""평단가·변동률·권역 집계. README.md '계산 규칙' 절의 공식을 그대로 구현한다.

핵심 규칙 (바꾸지 말 것):
- 그룹 평균은 산술평균(Σ건별 평단가 ÷ 건수)이 기본값. 가중평균은 검증용으로만 쓴다.
- 변동률 = 정책 후 산술평균 ÷ 정책 전 산술평균 − 1
- 최소 표본(구간별 30건 미만)은 화면에서 '표본 부족'으로 표시하고 랭킹에서 제외한다.
"""
from __future__ import annotations

import pandas as pd

from lib.theme import region_of

MIN_SAMPLE = 30


def arithmetic_avg(df: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame | float:
    if group_cols:
        g = df.groupby(group_cols)["평단가"]
        out = g.mean().reset_index(name="평단가_산술평균")
        out["거래건수"] = g.size().to_numpy()
        return out
    return df["평단가"].mean()


def weighted_avg(df: pd.DataFrame) -> float:
    """검증용. Σ거래금액 ÷ Σ전용면적(평) — 큰 면적 거래에 더 큰 가중치가 실린다."""
    py = df["전용면적"] / 3.3058
    return df["거래금액"].sum() / py.sum()


def change_rate(before: float, after: float) -> float | None:
    if before in (0, None) or pd.isna(before):
        return None
    return after / before - 1


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """월별 산술평균 평단가 + 거래건수. app.py 상단 콤보 차트에 사용."""
    out = (
        df.groupby("계약연월")
        .agg(평단가=("평단가", "mean"), 거래건수=("평단가", "size"))
        .reset_index()
        .sort_values("계약연월")
    )
    out["평단가"] = out["평단가"].round(1)
    return out


def gu_change_table(df: pd.DataFrame) -> pd.DataFrame:
    """구별 정책 전→후 평단가·거래량 변동률. 표본 부족 구는 '표본 부족' 플래그를 단다."""
    rows = []
    for gu, g in df.groupby("구"):
        before = g[g["정책여부"] == "정책전"]
        after = g[g["정책여부"] == "정책후"]
        n_before, n_after = len(before), len(after)
        low_sample = n_before < MIN_SAMPLE or n_after < MIN_SAMPLE
        avg_before = before["평단가"].mean() if n_before else None
        avg_after = after["평단가"].mean() if n_after else None
        price_rate = change_rate(avg_before, avg_after) if not low_sample else None
        volume_rate = change_rate(n_before, n_after) if not low_sample else None
        rows.append(
            {
                "구": gu,
                "권역": region_of(gu),
                "평단가_정책전": avg_before,
                "평단가_정책후": avg_after,
                "평단가_변동률": price_rate,
                "거래건수_정책전": n_before,
                "거래건수_정책후": n_after,
                "거래량_변동률": volume_rate,
                "표본부족": low_sample,
            }
        )
    return pd.DataFrame(rows).sort_values("평단가_변동률", ascending=False, na_position="last")


def region_summary(df: pd.DataFrame) -> pd.DataFrame:
    """4대 권역(강남3구/마용성/노도강/금관구) 전·후 비교. 나머지 구는 '기타'로 묶는다."""
    tmp = df.copy()
    tmp["권역"] = tmp["구"].map(region_of)
    rows = []
    for region, g in tmp.groupby("권역"):
        before = g[g["정책여부"] == "정책전"]
        after = g[g["정책여부"] == "정책후"]
        rows.append(
            {
                "권역": region,
                "평단가_정책전": before["평단가"].mean() if len(before) else None,
                "평단가_정책후": after["평단가"].mean() if len(after) else None,
                "평단가_변동률": change_rate(before["평단가"].mean(), after["평단가"].mean()) if len(before) and len(after) else None,
                "거래건수_정책전": len(before),
                "거래건수_정책후": len(after),
                "거래량_변동률": change_rate(len(before), len(after)) if len(before) else None,
            }
        )
    order = ["강남3구", "마용성", "노도강", "금관구", "기타"]
    out = pd.DataFrame(rows)
    out["권역"] = pd.Categorical(out["권역"], categories=order, ordered=True)
    return out.sort_values("권역").reset_index(drop=True)


def quadrant_data(df: pd.DataFrame) -> pd.DataFrame:
    """4분면 매트릭스용: 구별 (거래량 증감률 x, 평단가 변동률 y, 권역, 표본부족)."""
    table = gu_change_table(df)
    return table[["구", "권역", "거래량_변동률", "평단가_변동률", "표본부족"]].dropna(
        subset=["거래량_변동률", "평단가_변동률"]
    )


def policy_period_compare(df: pd.DataFrame, gu: str | None = None, dong: list[str] | None = None) -> dict:
    """정책 전·후 비교 페이지의 상단 KPI 두 장에 쓰는 요약."""
    sub = df
    if gu:
        sub = sub[sub["구"] == gu]
    if dong:
        sub = sub[sub["법정동"].isin(dong)]
    before = sub[sub["정책여부"] == "정책전"]
    after = sub[sub["정책여부"] == "정책후"]
    avg_before, avg_after = before["평단가"].mean(), after["평단가"].mean()
    return {
        "avg_before": avg_before,
        "avg_after": avg_after,
        "price_rate": change_rate(avg_before, avg_after),
        "count_before": len(before),
        "count_after": len(after),
        "count_rate": change_rate(len(before), len(after)),
        "low_sample": len(before) < MIN_SAMPLE or len(after) < MIN_SAMPLE,
    }


AMOUNT_BANDS = [
    (0, 30_000, "3억 미만"),
    (30_000, 60_000, "3~6억"),
    (60_000, 90_000, "6~9억"),
    (90_000, 120_000, "9~12억"),
    (120_000, float("inf"), "12억 이상"),
]


def amount_band_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """금액대별(억 단위) 거래 비중."""
    labels = [b[2] for b in AMOUNT_BANDS]
    edges = [b[0] for b in AMOUNT_BANDS] + [AMOUNT_BANDS[-1][1]]
    band = pd.cut(df["거래금액"], bins=edges, labels=labels, right=False)
    out = band.value_counts().reindex(labels).reset_index()
    out.columns = ["금액대", "건수"]
    out["비율"] = out["건수"] / out["건수"].sum()
    return out


def dong_change_table(df: pd.DataFrame, min_sample: int = MIN_SAMPLE) -> pd.DataFrame:
    """법정동 단위 정책 전→후 평단가·거래량 변동률 (최소 거래건수 미달 법정동은 제외)."""
    rows = []
    for (gu, dong), g in df.groupby(["구", "법정동"]):
        before = g[g["정책여부"] == "정책전"]
        after = g[g["정책여부"] == "정책후"]
        if len(before) < min_sample or len(after) < min_sample:
            continue
        rate = change_rate(before["평단가"].mean(), after["평단가"].mean())
        if rate is None:
            continue
        rows.append({
            "구": gu,
            "법정동": dong,
            "변동률": rate,
            "거래량_변동률": change_rate(len(before), len(after)),
            "거래건수": len(before) + len(after),
        })
    return pd.DataFrame(rows).sort_values("변동률", ascending=False)


def dong_ranking(df: pd.DataFrame, top_n: int = 10, min_sample: int = MIN_SAMPLE) -> tuple[pd.DataFrame, pd.DataFrame]:
    """법정동 상승 TOP N / 하락 TOP N."""
    ranked = dong_change_table(df, min_sample=min_sample)
    cols = ["구", "법정동", "변동률", "거래건수"]
    return ranked[cols].head(top_n), ranked[cols].tail(top_n).sort_values("변동률")
