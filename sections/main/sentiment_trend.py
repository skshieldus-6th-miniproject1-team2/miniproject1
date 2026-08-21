"""메인 대시보드 — 부동산 대책 시행 전후 감정 추이 (5일 단위 일평균)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import sentiment, theme


def render(news, shown_markers):
    st.subheader("부동산 대책 시행 전후 감정 추이")
    st.caption("5일 단위 일평균 뉴스 기사 수 · 감정 극성별")

    tagged = sentiment.add_group_column(news).dropna(subset=["날짜"])
    counts = (
        tagged.groupby([pd.Grouper(key="날짜", freq="5D"), "감정그룹"])
        .size()
        .unstack(fill_value=0)
    )
    for group in sentiment.GROUP_ORDER:
        if group not in counts.columns:
            counts[group] = 0
    daily_avg = counts[sentiment.GROUP_ORDER] / 5  # 5일 구간 합계를 일평균으로 환산

    color_map = {
        "긍정": theme.COLOR["sentiment_pos"],
        "중립": theme.COLOR["sentiment_neu"],
        "부정": theme.COLOR["sentiment_neg"],
    }

    fig = go.Figure()
    for group in ["부정", "중립", "긍정"]:
        fig.add_trace(go.Scatter(
            x=daily_avg.index, y=daily_avg[group], mode="lines+markers", name=group,
            line=dict(color=color_map[group], width=2.5), marker=dict(size=6),
        ))

    for label, date in shown_markers:
        ts = pd.Timestamp(date)
        if daily_avg.index.min() <= ts <= daily_avg.index.max():
            fig.add_vline(x=ts, line_dash="dash", line_color=theme.COLOR["policy_after"], line_width=2)
            # add_vline은 범례에 안 잡히므로 범례 전용 더미 트레이스를 하나 더 그린다
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode="lines",
                line=dict(color=theme.COLOR["policy_after"], dash="dash", width=2),
                name=f"대책 시행일 ({label})",
            ))

    fig.update_layout(**theme.plotly_layout(height=460))
    fig.update_xaxes(title_text="날짜", tickformat="%Y-%m-%d")
    fig.update_yaxes(title_text="일평균 뉴스 기사 수 (건)")
    theme.plotly_chart(fig)
