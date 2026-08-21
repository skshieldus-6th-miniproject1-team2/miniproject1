"""메인 대시보드 — 4대 권역 비교 (권역 구분 토글에 따라 25개 구 비교로도 전환)."""
import plotly.graph_objects as go
import streamlit as st

from lib import metrics, theme


def render(apt, gu_table, region_mode):
    if region_mode == "4대 권역":
        st.subheader("4대 권역 비교")
        compare_df = metrics.region_summary(apt).rename(columns={"권역": "구분"})
    else:
        st.subheader("25개 구 비교")
        compare_df = gu_table.rename(columns={"구": "구분"}).sort_values("평단가_변동률", ascending=True)

    fig_r = go.Figure()
    fig_r.add_trace(go.Bar(
        y=compare_df["구분"], x=compare_df["평단가_변동률"], orientation="h", name="평단가 변동률",
        marker_color=[theme.COLOR["up"] if v and v > 0 else theme.COLOR["down"] for v in compare_df["평단가_변동률"]],
    ))
    fig_r.update_layout(**theme.plotly_layout(height=230 if region_mode == "4대 권역" else 520, showlegend=False, title="평단가 변동률"))
    fig_r.update_xaxes(tickformat=".0%")
    theme.plotly_chart(fig_r)

    if region_mode == "4대 권역":
        fig_v = go.Figure()
        fig_v.add_trace(go.Bar(
            y=compare_df["구분"], x=compare_df["거래량_변동률"], orientation="h", name="거래량 변동률",
            marker_color=[theme.COLOR["up"] if v and v > 0 else theme.COLOR["down"] for v in compare_df["거래량_변동률"]],
        ))
        fig_v.update_layout(**theme.plotly_layout(height=230, showlegend=False, title="거래량 변동률"))
        fig_v.update_xaxes(tickformat=".0%")
        theme.plotly_chart(fig_v)
