"""지역별 변동률 — 법정동 변동률 TOP 10 / 하위 10 표."""
import streamlit as st

from lib import metrics


def render(apt, min_sample, unit):
    st.subheader("법정동 변동률 TOP 10 / 하위 10")
    top10, bottom10 = metrics.dong_ranking(apt, top_n=10, min_sample=min_sample)
    col_g, col_h = st.columns(2)
    with col_g:
        st.markdown("**상승 TOP 10**")
        st.dataframe(
            top10.assign(변동률=lambda d: d["변동률"].map(lambda v: f"{v:+.1%}")),
            hide_index=True, use_container_width=True,
        )
    with col_h:
        st.markdown("**하위 10**")
        st.dataframe(
            bottom10.assign(변동률=lambda d: d["변동률"].map(lambda v: f"{v:+.1%}")),
            hide_index=True, use_container_width=True,
        )

    if unit == "법정동" and (top10.empty and bottom10.empty):
        st.info(f"최소 거래건수 {min_sample}건을 만족하는 법정동이 없습니다. 슬라이더 값을 낮춰보세요.")
