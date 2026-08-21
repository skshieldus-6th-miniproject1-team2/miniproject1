"""정책 전·후 비교 사이드바 입력."""
import streamlit as st


def render_sidebar(apt_all):
    gu_list = sorted(apt_all["구"].unique())
    with st.sidebar:
        base_gu = st.selectbox("기준 자치구", gu_list, index=gu_list.index("성동구") if "성동구" in gu_list else 0)
        dong_options = sorted(apt_all.loc[apt_all["구"] == base_gu, "법정동"].unique())
        selected_dong = st.multiselect("법정동 선택", dong_options, default=dong_options[: min(2, len(dong_options))])
        compare_metric = st.radio("비교 지표", ["평단가", "거래량", "금액대"])
        size_band = st.selectbox("전용면적", ["전체 (소형·중형·대형)", "소형", "중형", "대형"])
        normalize = st.checkbox("동일 기간 정규화 (417일)", value=True)
        exclude_outlier = st.checkbox("이상치 거래 제외", value=True)

    return base_gu, selected_dong, compare_metric, size_band, normalize, exclude_outlier
