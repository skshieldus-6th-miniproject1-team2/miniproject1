"""뉴스·여론 분석 사이드바 입력 + 필터 적용."""
import streamlit as st

from sections.news.constants import GOV_OPTIONS, PHASE_OPTIONS, POLICY_OPTIONS


def render_sidebar(news_all):
    category_options = sorted(news_all["카테고리"].unique())

    with st.sidebar:
        target_policy = st.radio("대상 정책", ["전체"] + POLICY_OPTIONS, horizontal=False)
        phase_filter = st.selectbox("정책 시점", ["전체 시점"] + PHASE_OPTIONS)
        category_filter = st.multiselect("정책 카테고리", category_options)
        gov_filter = st.multiselect("표시 정부", GOV_OPTIONS, default=GOV_OPTIONS)
        min_prob = st.slider("확률 필터", 0.5, 0.99, 0.9, step=0.01)
        st.caption(f"확률 {min_prob:.2f} 이상만 표시")

    news = news_all.copy()
    if target_policy != "전체" and "정책" in news.columns:
        news = news[news["정책"] == target_policy]
    if phase_filter != "전체 시점":
        news = news[news["시기"] == phase_filter]
    if category_filter:
        news = news[news["카테고리"].isin(category_filter)]
    if gov_filter:
        news = news[news["정부"].isin(gov_filter)]
    news = news[news["수치"] >= min_prob]

    return news
