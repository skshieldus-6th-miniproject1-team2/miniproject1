"""정책 전·후 비교 — 기준 자치구 내 법정동별 변동률 + 상세표."""
import plotly.graph_objects as go
import streamlit as st

from lib import metrics, theme

# [수정 4] st.dataframe 렌더링 방식이므로 pandas Styler 대신 column_config로 정렬·너비를 지정.
# alignment="center"로 헤더·셀을 모두 가운데 정렬하고, 내용 길이에 맞춰 픽셀 너비를 좁힘.
_COLUMN_CONFIG = {
    "구": st.column_config.Column(width=90, alignment="center"),
    "법정동": st.column_config.Column(width=110, alignment="center"),
    "변동률": st.column_config.Column(width=90, alignment="center"),
    "거래량_변동률": st.column_config.Column(width=100, alignment="center"),
    "거래건수": st.column_config.Column(width=90, alignment="center"),
}


def render(apt, base_gu):
    st.subheader(f"{base_gu} 법정동별 변동률")
    dong_table = metrics.dong_change_table(apt[apt["구"] == base_gu], min_sample=10)
    if not len(dong_table):
        st.info(f"{base_gu}에는 정책 전·후 각 10건 이상 거래된 법정동이 없습니다.")
        return

    chart_height = max(280, 28 * len(dong_table))

    fig_dong = go.Figure(go.Bar(
        y=dong_table["법정동"], x=dong_table["변동률"], orientation="h",
        marker_color=[theme.COLOR["up"] if v > 0 else theme.COLOR["down"] for v in dong_table["변동률"]],
    ))
    fig_dong.update_layout(**theme.plotly_layout(height=chart_height, showlegend=False, xaxis_title="평단가 변동률"))
    fig_dong.update_xaxes(tickformat=".0%")

    col_i, col_j = st.columns([1, 1.6])
    with col_i:
        theme.plotly_chart(fig_dong)
    with col_j:
        st.dataframe(
            dong_table.assign(변동률=lambda d: d["변동률"].map(lambda v: f"{v:+.1%}"), 거래량_변동률=lambda d: d["거래량_변동률"].map(lambda v: f"{v:+.1%}" if v is not None else "N/A")),
            hide_index=True, use_container_width=False, height=chart_height, column_config=_COLUMN_CONFIG,
        )
