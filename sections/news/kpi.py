"""뉴스·여론 분석 — 수집 기사 / 감정 분석 완료 KPI."""
import streamlit as st


def render(total_collected, news_all):
    k1, k2 = st.columns(2)
    k1.metric("수집 기사", f"{total_collected:,}건", "부동산 정책 보도 · 4개 카테고리 (임시 데이터)")
    k2.metric("감정 분석 완료", f"{len(news_all):,}건", "4개 정부 비교 세트")
