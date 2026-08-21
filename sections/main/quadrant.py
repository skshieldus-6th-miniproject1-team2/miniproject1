"""메인 대시보드 — 4분면 매트릭스 (거래량 증감률 x 평단가 변동률, 색 = 권역)."""
import plotly.graph_objects as go
import streamlit as st

from lib import metrics, theme


def render(apt):
    st.subheader("거래량은 줄었는데 평단가는 올랐다")
    st.caption("자치구별 거래량 증감률(x) × 평단가 변동률(y) · 색 = 권역 · 음영 = 거래량↓·가격↑ 사분면")
    quad = metrics.quadrant_data(apt)
    top_left_n = int(((quad["거래량_변동률"] < 0) & (quad["평단가_변동률"] > 0)).sum())

    fig_q = go.Figure()
    for region, g in quad.groupby("권역"):
        fig_q.add_trace(
            go.Scatter(
                x=g["거래량_변동률"], y=g["평단가_변동률"], mode="markers+text",
                text=g["구"], textposition="top center", textfont=dict(size=10),
                marker=dict(size=11, color=theme.REGION_COLOR.get(region, theme.SERIES_OTHER)),
                name=region,
            )
        )
    fig_q.add_hline(y=0, line_color=theme.COLOR["border"])
    fig_q.add_vline(x=0, line_color=theme.COLOR["border"])
    x_min = quad["거래량_변동률"].min()
    y_max = quad["평단가_변동률"].max()
    fig_q.add_shape(type="rect", x0=x_min * 1.1, x1=0, y0=0, y1=y_max * 1.1, fillcolor=theme.COLOR["sentiment_neg"], opacity=0.06, line_width=0)
    fig_q.add_annotation(x=x_min * 1.05, y=y_max * 1.05, text=f"거래량↓·평단가↑ {top_left_n}곳", showarrow=False, font=dict(size=11, color=theme.COLOR["down"]), xanchor="left")
    fig_q.update_layout(**theme.plotly_layout(height=480, xaxis_title="거래량 증감률", yaxis_title="평단가 변동률"))
    fig_q.update_xaxes(tickformat=".0%")
    fig_q.update_yaxes(tickformat=".0%")
    theme.plotly_chart(fig_q)
