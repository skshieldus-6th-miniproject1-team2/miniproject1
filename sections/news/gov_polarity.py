"""뉴스·여론 분석 — 정부별 감정 극성 100% 누적 막대."""
import plotly.express as px
import streamlit as st

from lib import sentiment, theme
from sections.news.constants import GOV_OPTIONS


def render(news):
    st.subheader("정부별 감정 극성")
    ratio = sentiment.group_ratio(news, by=["정부"])
    fig_gov = px.bar(
        ratio, x="정부", y="비율", color="감정그룹", barmode="stack",
        category_orders={"정부": GOV_OPTIONS, "감정그룹": sentiment.GROUP_ORDER},
        color_discrete_map={"긍정": theme.COLOR["sentiment_pos"], "중립": theme.COLOR["sentiment_neu"], "부정": theme.COLOR["sentiment_neg"]},
    )
    fig_gov.update_layout(**theme.plotly_layout(height=300, bargap=0.3))
    fig_gov.update_yaxes(tickformat=".0%")
    theme.plotly_chart(fig_gov)
