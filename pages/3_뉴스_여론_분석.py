"""4. 뉴스·여론 분석 — 정책 보도의 감정 분포와 기사 원문 탐색.

각 섹션의 실제 렌더링 코드는 sections/news/ 아래 파일로 나눠져 있다.
"""
import streamlit as st

from lib import load, theme
from sections.news import article_explorer, collection, emotion_bar, kpi, phase_table, policy_polarity, sidebar

theme.inject_css()
theme.render_logo()
load.guard_news_or_stop()

st.title("뉴스 · 여론 분석")

news_full = load.load_news_perspective()  # 전체 수집분 (정책·단계 포함, 7종 감정 없음)
news_with_emotion = load.load_news_articles()  # 7종 감정이 붙은 결합분 (10·15 일부 누락 — 아래 안내 참고)
st.caption(f"정책 보도 {len(news_full):,}건의 감정 분포와 기사 원문 탐색")

news = sidebar.render_sidebar(news_with_emotion)

kpi.render(news_full, news_with_emotion)
st.divider()

collection.render(news_full)
st.divider()

col_left, col_right = st.columns([3, 2])
with col_left:
    phase_table.render(news)
with col_right:
    emotion_bar.render(news)
st.caption(
    "⚠️ 7종 감정 분석은 News_Scraping_retouch.csv 기준(~2025-09-26)까지만 처리돼 있어, "
    "10·15 대책 기사(9/28~) 는 이 표·차트에서 빠져 있습니다."
)
st.divider()

policy_polarity.render(load.load_news_perspective_summary())
st.divider()

article_explorer.render(news)

st.divider()
st.subheader("댓글 감정 분석")
st.info("예정 — 댓글 수집·분석 파이프라인이 확정되면 이 절에 추가합니다.")

st.caption("데이터: j_News_Scraping.csv, News_Scraping_retouch.csv (url 기준 결합), j_News_Scraping_summary.csv.")
