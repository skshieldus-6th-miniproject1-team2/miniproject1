"""정책 전·후 비교 — 전용면적별 비교 (비교 지표 라디오에 따라 거래량/평단가/금액대로 전환)."""
import plotly.graph_objects as go
import streamlit as st

from lib import metrics, theme

AREA_ORDER = ["소형 (60㎡ 미만)", "중형 (60~100㎡)", "대형 (100㎡ 이상)"]


def _area_bin(a: float) -> str:
    if a < 60:
        return "소형 (60㎡ 미만)"
    if a < 100:
        return "중형 (60~100㎡)"
    return "대형 (100㎡ 이상)"


def render(target, before, after, compare_metric):
    if not len(target):
        st.info("선택한 조건에 해당하는 거래가 없습니다.")
        return

    tmp = target.copy()
    tmp["면적구분"] = tmp["전용면적"].map(_area_bin)

    if compare_metric == "금액대":
        st.subheader("금액대별 거래 비중 변화")
        band_before = metrics.amount_band_distribution(before) if len(before) else None
        band_after = metrics.amount_band_distribution(after) if len(after) else None
        fig_area = go.Figure()
        if band_before is not None:
            fig_area.add_trace(go.Bar(x=band_before["금액대"], y=band_before["비율"], name="정책 전", marker_color=theme.COLOR["policy_before"]))
        if band_after is not None:
            fig_area.add_trace(go.Bar(x=band_after["금액대"], y=band_after["비율"], name="정책 후", marker_color=theme.COLOR["policy_after"]))
        fig_area.update_layout(**theme.plotly_layout(height=360, barmode="group"))
        fig_area.update_yaxes(tickformat=".0%")
    elif compare_metric == "평단가":
        st.subheader("전용면적별 평단가 변화")
        area_price = tmp.groupby(["면적구분", "정책여부"])["평단가"].mean().unstack(fill_value=None).reindex(AREA_ORDER)
        fig_area = go.Figure()
        fig_area.add_trace(go.Bar(x=area_price.index, y=area_price.get("정책전"), name="정책 전", marker_color=theme.COLOR["policy_before"]))
        fig_area.add_trace(go.Bar(x=area_price.index, y=area_price.get("정책후"), name="정책 후", marker_color=theme.COLOR["policy_after"]))
        fig_area.update_layout(**theme.plotly_layout(height=360, barmode="group", yaxis_title="만원/평"))
    else:
        st.subheader("전용면적별 거래량 변화")
        area_counts = tmp.groupby(["면적구분", "정책여부"]).size().unstack(fill_value=0).reindex(AREA_ORDER)
        fig_area = go.Figure()
        fig_area.add_trace(go.Bar(x=area_counts.index, y=area_counts.get("정책전"), name="정책 전", marker_color=theme.COLOR["policy_before"]))
        fig_area.add_trace(go.Bar(x=area_counts.index, y=area_counts.get("정책후"), name="정책 후", marker_color=theme.COLOR["policy_after"]))
        fig_area.update_layout(**theme.plotly_layout(height=360, barmode="group"))

    st.plotly_chart(fig_area, use_container_width=True)
