"""뉴스·여론 분석 — 기사 수집 구성 (정책별).

7종 감정 분석(News_Scraping_retouch.csv)은 2025-09-26까지만 돼 있어서, 그 이후에 시작하는
10·15 대책 기사가 감정 조인 결과에서 통째로 빠진다. 이 섹션은 수집량 자체를 보여주는
곳이라 감정 조인 없이 j_News_Scraping.csv(전체 수집분)를 그대로 쓴다.
"""
import streamlit as st

from sections.news.constants import POLICY_OPTIONS


def render(news_full):
    st.subheader("기사 수집 구성")
    st.caption("정책별 수집 기사 수 (평시 = 정책 발표 전후가 아닌 일반 시기)")

    policy_counts = news_full["정책"].value_counts().reindex(POLICY_OPTIONS).fillna(0)
    for policy, count in policy_counts.items():
        ratio = count / len(news_full)
        st.markdown(f"**{policy}** &nbsp; {int(count)}건 · {ratio:.1%}")
        st.progress(ratio)
