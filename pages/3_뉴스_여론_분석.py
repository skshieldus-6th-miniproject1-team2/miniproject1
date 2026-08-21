"""4. 뉴스·여론 분석 — 정책 보도의 감정 분포와 기사 원문 탐색.

각 섹션의 실제 렌더링 코드는 sections/news/ 아래 파일로 나눠져 있다.
"""
import streamlit as st

from lib import load, theme
from sections.news import article_explorer, kpi, policy_polarity, sidebar

theme.inject_css()
theme.render_logo()
load.guard_news_or_stop()

st.title("뉴스 · 여론 분석")

news_full = load.load_news_perspective()  # 전체 수집분 (정책·단계 포함, 감정 없음)
news_with_emotion = load.load_news_articles()  # 감정 3그룹(긍정/중립/부정)이 붙은 결합분
st.caption(f"정책 보도 {len(news_full):,}건의 감정 분포와 기사 원문 탐색")

news = sidebar.render_sidebar(news_with_emotion)

kpi.render(news_full, news_with_emotion)
st.divider()

policy_polarity.render(news_full)
st.divider()

article_explorer.render(news)

st.caption("데이터: j_News_Scraping.csv, News_Scraping.csv (url 기준 결합).")
