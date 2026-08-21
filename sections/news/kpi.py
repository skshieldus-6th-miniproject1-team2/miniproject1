"""뉴스·여론 분석 — 수집 기사 / 부정 감정 비중 KPI."""
import streamlit as st

from lib import sentiment


def render(news_full, news_with_emotion):
    group_counts = sentiment.add_group_column(news_with_emotion)["감정그룹"].value_counts()
    neg_ratio = group_counts.get("부정", 0) / group_counts.sum()

    k1, k2 = st.columns(2)
    k1.metric("수집 기사", f"{len(news_full):,}건", "정책 3건(6·27·9·7·10·15) + 평시")
    k2.metric("부정 감정 비중", f"{neg_ratio:.1%}", f"감정 분석 완료 {len(news_with_emotion):,}건 기준")
