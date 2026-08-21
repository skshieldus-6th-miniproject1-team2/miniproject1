"""뉴스·여론 분석 — 세부 감정 분포(7종) 막대."""
import plotly.express as px
import streamlit as st

from lib import sentiment, theme


def render(news):
    st.subheader("세부 감정 분포")
    emo_counts = news["감정"].value_counts().reindex(sentiment.EMOTIONS_7).fillna(0)
    fig_emo = px.bar(x=emo_counts.index, y=emo_counts.values, color=emo_counts.index, color_discrete_sequence=theme.SERIES + [theme.SERIES_OTHER])
    fig_emo.update_layout(**theme.plotly_layout(height=340, showlegend=False, xaxis_title=None, yaxis_title="건수"))
    theme.plotly_chart(fig_emo, use_container_width=True)
