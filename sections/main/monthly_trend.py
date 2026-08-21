"""메인 대시보드 — 월별 평단가 + 거래량 콤보차트, 정책 마커 점선."""
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from lib import metrics, theme


def render(apt_view, shown_markers):
    st.subheader("월별 서울 평균 평단가와 거래량")
    st.caption("위 = 산술평균 평단가(만원/평), 아래 = 월 거래건수 · 같은 x축을 공유하되 축은 겹치지 않는다")

    monthly = metrics.monthly_trend(apt_view)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.06)
    fig.add_trace(
        go.Scatter(x=monthly["계약연월"], y=monthly["평단가"], mode="lines", line=dict(color=theme.COLOR["brand"], width=3), name="평단가"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(x=monthly["계약연월"], y=monthly["거래건수"], marker_color=theme.COLOR["policy_before"], name="거래건수"),
        row=2, col=1,
    )
    visible_markers = [(label, date) for label, date in shown_markers if monthly["계약연월"].min() <= date[:7] <= monthly["계약연월"].max()]
    for i, (label, date) in enumerate(visible_markers):
        fig.add_vline(x=date[:7], line_dash="dash", line_color=theme.COLOR["text_faint"], row=1, col=1)
        # 인접한 정책 마커끼리 라벨이 겹치지 않도록 위아래로 번갈아 배치한다
        fig.add_annotation(x=date[:7], y=1, yref="paper", text=label, showarrow=False, yshift=10 + (i % 2) * 16, font=dict(size=10, color=theme.COLOR["text_muted"]))
    fig.update_layout(**theme.plotly_layout(height=460, showlegend=False))
    # 평단가 라인은 Plotly 기본 여백이 넉넉해서 확대/축소 시 실제 데이터보다 위아래 공백이 크게 느껴진다.
    # 데이터 범위 기준으로 여백을 좁게 고정한다.
    price_min, price_max = monthly["평단가"].min(), monthly["평단가"].max()
    price_pad = (price_max - price_min) * 0.08 or price_max * 0.02
    fig.update_yaxes(title_text="만원/평", range=[price_min - price_pad, price_max + price_pad], row=1, col=1)
    fig.update_yaxes(title_text="거래건수", row=2, col=1)
    theme.plotly_chart(fig)
