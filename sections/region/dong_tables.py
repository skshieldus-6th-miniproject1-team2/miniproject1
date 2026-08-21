"""지역별 변동률 — 법정동 변동률 TOP 10 / 하위 10 표."""
import streamlit as st

from lib import metrics

# column_config로 정렬·너비를 지정: alignment="center"로 헤더·셀을 가운데 정렬하고,
# 내용 길이에 맞춰 픽셀 너비를 좁힌다. use_container_width=False라야 지정한 너비가 실제로
# 반영된다(True면 남는 공간이 컬럼에 균등 재배분되어 너비 지정이 무의미해진다).
_COLUMN_CONFIG = {
    "구": st.column_config.Column(width=90, alignment="center"),
    "법정동": st.column_config.Column(width=110, alignment="center"),
    "변동률": st.column_config.Column(width=90, alignment="center"),
    "거래건수": st.column_config.Column(width=90, alignment="center"),
}


def render(apt, min_sample, unit):
    st.subheader("법정동 변동률 TOP 10 / 하위 10")
    top10, bottom10 = metrics.dong_ranking(apt, top_n=10, min_sample=min_sample)
    col_g, col_h = st.columns(2)
    with col_g:
        st.markdown("**상승 TOP 10**")
        st.dataframe(
            top10.assign(변동률=lambda d: d["변동률"].map(lambda v: f"{v:+.1%}")),
            hide_index=True, use_container_width=False, column_config=_COLUMN_CONFIG,
        )
    with col_h:
        st.markdown("**하위 10**")
        st.dataframe(
            bottom10.assign(변동률=lambda d: d["변동률"].map(lambda v: f"{v:+.1%}")),
            hide_index=True, use_container_width=False, column_config=_COLUMN_CONFIG,
        )

    if unit == "법정동" and (top10.empty and bottom10.empty):
        st.info(f"최소 거래건수 {min_sample}건을 만족하는 법정동이 없습니다. 슬라이더 값을 낮춰보세요.")
