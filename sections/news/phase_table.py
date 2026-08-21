"""뉴스·여론 분석 — 단계별 감정 분포 교차표."""
import streamlit as st

from lib import sentiment
from sections.news.constants import PHASE_OPTIONS


def render(news):
    st.subheader("단계별 감정 분포")
    st.caption("기사 수 · 현재 필터 기준")
    tab = news.groupby(["단계", "감정"]).size().unstack(fill_value=0).reindex(PHASE_OPTIONS).reindex(columns=sentiment.EMOTIONS_7, fill_value=0)
    st.dataframe(tab, use_container_width=False)
