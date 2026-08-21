"""정책 전·후 비교 — KPI 4개 (평단가, 거래건수, 평균 전용면적, 자치구 상승률 순위)."""
import streamlit as st

from lib import metrics


def render(apt, base_gu, summary, before, after, area_before, area_after):
    # metric의 델타(3번째 값)를 넷 다 채워야 카드 세로 길이가 맞는다 — 델타를 안 주면 그 줄이 통째로 빠진다.
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("평균 평단가 (만원/평)", f"{summary['avg_before']:,.0f} → {summary['avg_after']:,.0f}", f"{summary['price_rate']:+.1%}" if summary["price_rate"] is not None else "N/A")
    k2.metric("거래 건수 (건)", f"{summary['count_before']:,.0f} → {summary['count_after']:,.0f}", f"{summary['count_rate']:+.1%}" if summary["count_rate"] is not None else "N/A")

    area_rate = metrics.change_rate(area_before, area_after) if len(before) and len(after) else None
    k3.metric(
        "평균 전용면적 (㎡)",
        f"{area_before:,.1f} → {area_after:,.1f}" if len(before) and len(after) else "N/A",
        f"{area_rate:+.1%}" if area_rate is not None else "N/A",
    )

    gu_rank_table = metrics.gu_change_table(apt).dropna(subset=["평단가_변동률"]).reset_index(drop=True)
    gu_rank_table["순위"] = gu_rank_table["평단가_변동률"].rank(ascending=False, method="min").astype(int)
    rank_row = gu_rank_table[gu_rank_table["구"] == base_gu]
    total_gu = len(gu_rank_table)
    if len(rank_row):
        rank = int(rank_row["순위"].iloc[0])
        rank_text, percentile_text = f"{rank} / {total_gu}", f"상위 {rank / total_gu:.0%}"
    else:
        rank_text, percentile_text = "N/A", "N/A"
    k4.metric("자치구 상승률 순위", rank_text, percentile_text)

    if summary["low_sample"]:
        st.caption(f"⚠️ 정책 전·후 거래건수가 {metrics.MIN_SAMPLE}건 미만이라 평균이 흔들릴 수 있습니다.")
