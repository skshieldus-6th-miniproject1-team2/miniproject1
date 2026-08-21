"""메인 대시보드 — KPI 4개 (평균 평단가, 거래 건수, 상승 자치구 수, 뉴스 부정 감정 비중)."""
import streamlit as st

from lib import metrics, sentiment


def render(apt, gu_table, news):
    overall_before = apt[apt["정책여부"] == "정책전"]["평단가"].mean()
    overall_after = apt[apt["정책여부"] == "정책후"]["평단가"].mean()
    overall_rate = metrics.change_rate(overall_before, overall_after)
    count_before, count_after = (apt["정책여부"] == "정책전").sum(), (apt["정책여부"] == "정책후").sum()
    count_rate = metrics.change_rate(count_before, count_after)
    up_gu = int((gu_table["평단가_변동률"] > 0).sum())
    total_gu = int(gu_table["평단가_변동률"].notna().sum())
    group_counts = sentiment.add_group_column(news)["감정그룹"].value_counts()
    neg_pct_overall = group_counts.get("부정", 0) / group_counts.sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("서울 평균 평단가 (정책 후)", f"{overall_after:,.0f} 만원/평", f"{overall_rate:+.1%}")
    k2.metric("전체 거래 건수", f"{count_after:,.0f} 건", f"{count_rate:+.1%}")
    k3.metric("상승 자치구 수", f"{up_gu} / {total_gu}")
    k4.metric("뉴스 부정 감정 비중", f"{neg_pct_overall:.1%}")
