"""정책 전·후 비교 — 기준 자치구 월별 평단가·거래량, 시행일 세로선."""
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from lib import metrics, theme


def render(base_gu, target, apt, before, after):
    st.subheader(f"{base_gu} 월별 평단가 · 거래량")
    st.caption("위 = 평균 평단가(만원/평), 아래 = 월 거래건수")
    monthly = metrics.monthly_trend(target) if len(target) else metrics.monthly_trend(apt.iloc[0:0])
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.06)
    fig.add_trace(go.Scatter(x=monthly["계약연월"], y=monthly["평단가"], mode="lines+markers", line=dict(color=theme.COLOR["policy_after"], width=3), name="평단가"), row=1, col=1)
    fig.add_trace(go.Bar(x=monthly["계약연월"], y=monthly["거래건수"], marker_color=theme.COLOR["policy_before"], name="거래건수"), row=2, col=1)
    fig.add_vline(x="2025-06", line_dash="dash", line_color=theme.COLOR["brand"], row=1, col=1)
    fig.add_annotation(x="2025-06", y=1, yref="paper", text="2025-06-28 정책 시행", showarrow=False, yshift=10, font=dict(size=11, color=theme.COLOR["brand"]))
    fig.update_layout(**theme.plotly_layout(height=440, showlegend=False))
    theme.plotly_chart(fig)

    if len(before) and len(after):
        st.caption(
            f"평단가는 정책 이후 {before['평단가'].mean():,.0f} → {after['평단가'].mean():,.0f}만원/평으로 변했고, "
            f"거래건수는 {len(before):,}건 → {len(after):,}건으로 변했습니다."
        )
