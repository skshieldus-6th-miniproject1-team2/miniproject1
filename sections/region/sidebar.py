"""지역별 변동률 사이드바 입력."""
import streamlit as st

from lib import theme


def render_sidebar():
    with st.sidebar:
        unit = st.radio("집계 단위", ["자치구", "법정동"])
        sort_key = st.selectbox("정렬 기준", ["변동률 높은 순", "변동률 낮은 순", "거래건수 많은 순"])
        min_sample = st.slider("최소 거래건수 (동 단위 신뢰 구간)", min_value=10, max_value=100, value=30, step=5)
        st.caption(f"{min_sample}건 이상 (정책 전·후 각각 기준)")
        region_filter = st.multiselect("권역 필터", list(theme.REGION_GROUPS.keys()))
        exclude_outlier = st.checkbox("이상치 거래 제외", value=True)

    return unit, sort_key, min_sample, region_filter, exclude_outlier
