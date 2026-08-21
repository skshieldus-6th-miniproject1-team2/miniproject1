"""메인 대시보드 — 4개 정부 감정 극성 100% 누적 막대."""
import plotly.graph_objects as go
import streamlit as st

from lib import sentiment, theme

GOV_ORDER = ["박근혜", "문재인", "윤석열", "이재명"]


def render(news):
    st.subheader("대중 반응")
    st.caption("4개 정부 감정 극성 100% 누적 막대")
    ratio = sentiment.group_ratio(news, by=["정부"])
    fig_s = go.Figure()
    for grp, color in zip(sentiment.GROUP_ORDER, [theme.COLOR["sentiment_pos"], theme.COLOR["sentiment_neu"], theme.COLOR["sentiment_neg"]]):
        sub = ratio[ratio["감정그룹"] == grp].set_index("정부").reindex(GOV_ORDER)
        fig_s.add_trace(go.Bar(x=GOV_ORDER, y=sub["비율"], name=grp, marker_color=color))
    fig_s.update_layout(**theme.plotly_layout(height=340, barmode="stack"))
    fig_s.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_s, use_container_width=True)
