"""4. 뉴스·여론 분석 — 정책 보도의 감정 분포와 기사 원문 탐색.

각 섹션의 실제 렌더링 코드는 sections/news/ 아래 파일로 나눠져 있다.
"""
import streamlit as st

from lib import load, theme
from sections.news import article_explorer, collection, emotion_bar, gov_polarity, kpi, phase_table, sidebar

theme.inject_css()
theme.render_logo()
load.guard_or_stop()

st.title("뉴스 · 여론 분석")

news_all = load.load_news("category")
total_collected = len(news_all)
st.caption(f"정책 보도 {total_collected:,}건의 감정 분포와 기사 원문 탐색")

news = sidebar.render_sidebar(news_all)

kpi.render(total_collected, news_all)
st.divider()

collection.render(news_all)
st.divider()

col_left, col_right = st.columns([3, 2])
with col_left:
    phase_table.render(news)
with col_right:
    emotion_bar.render(news)
st.divider()

col_gov, _ = st.columns([1, 1])
with col_gov:
    gov_polarity.render(news)
st.divider()

article_explorer.render(news)

st.divider()
st.subheader("댓글 감정 분석")
st.info("예정 — 댓글 수집·분석 파이프라인이 확정되면 이 절에 추가합니다.")

st.caption("데이터: news_titles_category.csv (현재는 화면 검증용 임시 데이터, 컬럼 구성은 확정 전).")
