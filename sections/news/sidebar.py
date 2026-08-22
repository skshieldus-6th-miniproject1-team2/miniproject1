"""뉴스·여론 분석 사이드바 입력 + 필터 적용.

'정책 카테고리'(공급/세제/대출/시장안정)와 '표시 정부'(박근혜~이재명) 필터는 실제 데이터에
해당 컬럼이 없어서 뺐다 — 관점(기업/소비자/시장) 비교는 정책·관점 극성 섹션에서 별도로 다룬다.
"""
import streamlit as st

from sections.news.constants import PHASE_OPTIONS, POLICY_OPTIONS


def render_sidebar(news_all):
    with st.sidebar:
        target_policy = st.radio("대상 정책", ["전체"] + POLICY_OPTIONS, horizontal=False)
        phase_filter = st.selectbox("정책 시점", ["전체 시점"] + PHASE_OPTIONS)

    news = news_all.copy()
    if target_policy != "전체":
        news = news[news["정책"] == target_policy]
    if phase_filter != "전체 시점":
        news = news[news["단계"] == phase_filter]

    return news
