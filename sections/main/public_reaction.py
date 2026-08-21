"""메인 대시보드 — 정책별 감정 극성 100% 누적 막대 (구 '4개 정부 감정 극성').

실제 뉴스 데이터에는 정부 비교 축이 없어 정책(6·27/9·7/10·15/평시) 축으로 바꿨다.
"""
import plotly.graph_objects as go
import streamlit as st

from lib import sentiment, theme

POLICY_ORDER = ["6·27", "9·7", "10·15", "평시"]


def render(news):
    st.subheader("대중 반응")
    st.caption("정책별 감정 극성 100% 누적 막대")
    ratio = sentiment.group_ratio(news, by=["정책"])
    fig_s = go.Figure()
    for grp, color in zip(sentiment.GROUP_ORDER, [theme.COLOR["sentiment_pos"], theme.COLOR["sentiment_neu"], theme.COLOR["sentiment_neg"]]):
        sub = ratio[ratio["감정그룹"] == grp].set_index("정책").reindex(POLICY_ORDER)
        fig_s.add_trace(go.Bar(x=POLICY_ORDER, y=sub["비율"], name=grp, marker_color=color))
    fig_s.update_layout(**theme.plotly_layout(height=340, barmode="stack"))
    fig_s.update_yaxes(tickformat=".0%")
    theme.plotly_chart(fig_s)
