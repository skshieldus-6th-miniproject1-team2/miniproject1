"""메인 대시보드 — 보도 단계 분포 (평시 / 시행 전 / 시행일 / 초기 반응).

실제 데이터의 '단계'는 시행 후 장기 반응(체감반응) 없이 3개 정책 공통으로 시행일 직후
초기반응까지만 수집돼 있어, 원래의 3단계(시행 전 / 발표 후·시행 전 / 시행 후) 버킷 대신
실제 4단계를 그대로 보여준다.
"""
import plotly.graph_objects as go
import streamlit as st

from lib import theme
from sections.news.constants import PHASE_OPTIONS


def render(news):
    st.subheader("보도 단계 분포")
    st.caption("평시 / 시행 전 / 시행일 / 초기 반응 (3개 정책 통합)")
    counts = news["단계"].value_counts().reindex(PHASE_OPTIONS).fillna(0)
    fig_p = go.Figure(go.Bar(x=counts.index, y=counts.values, marker_color=theme.COLOR["brand"]))
    fig_p.update_layout(**theme.plotly_layout(height=340, showlegend=False, bargap=0.55))
    # 막대 4개가 전체 폭에 퍼져 헐렁해 보이던 문제: 가운데 컬럼으로 좁혀서 표시한다.
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        theme.plotly_chart(fig_p)
