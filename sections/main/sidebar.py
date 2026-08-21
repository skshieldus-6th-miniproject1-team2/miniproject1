"""메인 대시보드 사이드바 입력."""
import streamlit as st

from lib import theme


def render_sidebar():
    with st.sidebar:
        st.markdown("### 분석 구간")
        period = st.radio("분석 구간", ["정책 전", "정책 후", "전체"], index=2, label_visibility="collapsed")

        st.markdown("### 표시 정책 마커")
        marker_cols = st.columns(2)
        shown_markers = []
        for i, (label, date) in enumerate(theme.POLICY_MARKERS.items()):
            with marker_cols[i % 2]:
                if st.checkbox(label, value=True, key=f"marker_{label}"):
                    shown_markers.append((label, date))

        st.markdown("### 권역 구분")
        region_mode = st.radio("권역 구분", ["4대 권역", "25개 구"], label_visibility="collapsed")

        st.markdown("### ")
        exclude_outlier = st.checkbox("이상치 거래 제외", value=True)
        exclude_unsettled = st.checkbox("미집계 월 제외 (2026-08)", value=True)

    return period, shown_markers, region_mode, exclude_outlier, exclude_unsettled
