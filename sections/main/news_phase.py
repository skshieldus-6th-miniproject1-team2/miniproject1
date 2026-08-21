"""메인 대시보드 — 보도 시점 분포 (시행 전 / 발표 후·시행 전 / 시행 후)."""
import plotly.graph_objects as go
import streamlit as st

from lib import theme

# 4단계 시기 컬럼을 메인 화면이 요구하는 3단계로 묶는다 (README '화면 구성' 표 기준)
PHASE_MAP = {"시행 전": "시행 전", "시행일": "발표 후·시행 전", "초기 반응": "발표 후·시행 전", "체감 반응": "시행 후"}
PHASE_ORDER = ["시행 전", "발표 후·시행 전", "시행 후"]


def render(news):
    st.subheader("보도 시점 분포")
    st.caption("시행 전 / 발표 후·시행 전 / 시행 후 (잠정 — 뉴스 소스 확정 후 갱신 예정)")
    news_phase = news.copy()
    news_phase["3단계"] = news_phase["시기"].map(PHASE_MAP)
    counts = news_phase["3단계"].value_counts().reindex(PHASE_ORDER).fillna(0)
    fig_p = go.Figure(go.Bar(x=counts.index, y=counts.values, marker_color=theme.COLOR["brand"]))
    fig_p.update_layout(**theme.plotly_layout(height=340, showlegend=False))
    st.plotly_chart(fig_p, use_container_width=True)
