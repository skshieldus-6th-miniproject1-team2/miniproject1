"""뉴스·여론 분석 — 관점별 감정 추이 (5일 단위 일평균 선 그래프).

j_News_Scraping.csv 전체(정책 구분 없이 날짜 전체)를 쓴다. 기업/시장 관점은 라디오로 고른다
(소비자 관점은 화면에서 뺐다 — j_News_Scraping_summary.csv 참고 시 필요하면 다시 켤 수 있다).
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import theme
from sections.news.constants import PERSPECTIVE_OPTIONS

# j_News_Scraping.csv 기준 실제 시행일 (6·27_시행일 / 9·7_시행일 / 10·15_시행일의 날짜)
POLICY_DATES = [("6·27", "2025-06-28"), ("9·7", "2025-09-08"), ("10·15", "2025-10-16")]
GROUP_ORDER = ["부정", "중립", "긍정"]
COLOR_MAP = {"부정": theme.COLOR["sentiment_neg"], "중립": theme.COLOR["sentiment_neu"], "긍정": theme.COLOR["sentiment_pos"]}


def render(news_full):
    st.subheader("관점별 감정 추이")

    perspective = st.radio("관점", PERSPECTIVE_OPTIONS, horizontal=True)
    st.caption(f"[{perspective} 관점] 5일 단위 일평균 뉴스 기사 수 · 감정 극성별")

    emo_col = f"{perspective}_감정"
    df = news_full.dropna(subset=["날짜"])
    counts = (
        df.groupby([pd.Grouper(key="날짜", freq="5D"), emo_col])
        .size()
        .unstack(fill_value=0)
    )
    for group in GROUP_ORDER:
        if group not in counts.columns:
            counts[group] = 0
    daily_avg = counts[GROUP_ORDER] / 5  # 5일 구간 합계를 일평균으로 환산

    fig = go.Figure()
    for group in GROUP_ORDER:
        fig.add_trace(go.Scatter(
            x=daily_avg.index, y=daily_avg[group], mode="lines+markers", name=group,
            line=dict(color=COLOR_MAP[group], width=2.5), marker=dict(size=5),
        ))

    for label, date in POLICY_DATES:
        ts = pd.Timestamp(date)
        if daily_avg.index.min() <= ts <= daily_avg.index.max():
            fig.add_vline(x=ts, line_dash="dash", line_color=theme.COLOR["policy_after"], line_width=2)
            # add_vline은 범례에 안 잡히므로 범례 전용 더미 트레이스를 하나 더 그린다
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode="lines",
                line=dict(color=theme.COLOR["policy_after"], dash="dash", width=2),
                name=f"대책 시행일 ({date})",
            ))

    fig.update_layout(**theme.plotly_layout(height=420))
    fig.update_xaxes(title_text="날짜", tickformat="%Y-%m-%d")
    fig.update_yaxes(title_text="일평균 뉴스 기사 수 (건)")
    theme.plotly_chart(fig)
