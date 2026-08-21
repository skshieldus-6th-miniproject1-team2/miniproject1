"""메인 대시보드 — 정책별 감정 극성 100% 누적 막대 (구 '4개 정부 감정 극성').

실제 뉴스 데이터에는 정부 비교 축이 없어 정책(6·27/9·7/10·15/평시) 축으로 바꿨다.
정책별로 감정 데이터가 비어 있는 경우를 대비해, 데이터가 있는 정책만 동적으로 표시한다.
"""
import plotly.graph_objects as go
import streamlit as st

from lib import sentiment, theme

POLICY_ORDER = ["6·27", "9·7", "10·15", "평시"]


def render(news):
    st.subheader("대중 반응")
    ratio = sentiment.group_ratio(news, by=["정책"])
    available = set(ratio["정책"])
    policies = [p for p in POLICY_ORDER if p in available]
    missing = [p for p in POLICY_ORDER if p not in available]

    caption = "정책별 감정 극성 100% 누적 막대"
    if missing:
        caption += f" (감정 데이터 없음: {', '.join(missing)})"
    st.caption(caption)

    if not policies:
        st.info("표시할 감정 데이터가 없습니다.")
        return

    fig_s = go.Figure()
    for grp, color in zip(sentiment.GROUP_ORDER, [theme.COLOR["sentiment_pos"], theme.COLOR["sentiment_neu"], theme.COLOR["sentiment_neg"]]):
        sub = ratio[ratio["감정그룹"] == grp].set_index("정책").reindex(policies)
        fig_s.add_trace(go.Bar(x=policies, y=sub["비율"], name=grp, marker_color=color))
    fig_s.update_layout(**theme.plotly_layout(height=340, barmode="stack", bargap=0.55))
    fig_s.update_yaxes(tickformat=".0%")
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        theme.plotly_chart(fig_s)
