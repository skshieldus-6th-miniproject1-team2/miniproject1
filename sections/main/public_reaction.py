<<<<<<< Updated upstream
"""메인 대시보드 — 4개 정부 감정 극성 100% 누적 막대."""
=======
"""메인 대시보드 — 정책별 감정 극성 100% 누적 막대 (구 '4개 정부 감정 극성').

실제 뉴스 데이터에는 정부 비교 축이 없어 정책(6·27/9·7/10·15/평시) 축으로 바꿨다.
10·15 시기 기사는 감정 소스(News_Scraping_retouch.csv)와 url이 하나도 겹치지 않아
load.load_news_articles()의 inner merge에서 통째로 빠진다 — 감정 극성을 낼 데이터 자체가
없다는 뜻이라, 빈 막대를 그리는 대신 그 정책을 축에서 빼고 캡션에 이유를 밝힌다.
"""
>>>>>>> Stashed changes
import plotly.graph_objects as go
import streamlit as st

from lib import sentiment, theme

GOV_ORDER = ["박근혜", "문재인", "윤석열", "이재명"]


def render(news):
    st.subheader("대중 반응")
<<<<<<< Updated upstream
    st.caption("4개 정부 감정 극성 100% 누적 막대")
    ratio = sentiment.group_ratio(news, by=["정부"])
    fig_s = go.Figure()
    for grp, color in zip(sentiment.GROUP_ORDER, [theme.COLOR["sentiment_pos"], theme.COLOR["sentiment_neu"], theme.COLOR["sentiment_neg"]]):
        sub = ratio[ratio["감정그룹"] == grp].set_index("정부").reindex(GOV_ORDER)
        fig_s.add_trace(go.Bar(x=GOV_ORDER, y=sub["비율"], name=grp, marker_color=color))
    fig_s.update_layout(**theme.plotly_layout(height=340, barmode="stack"))
=======
    ratio = sentiment.group_ratio(news, by=["정책"])
    available = set(ratio["정책"])
    policies = [p for p in POLICY_ORDER if p in available]
    missing = [p for p in POLICY_ORDER if p not in available]

    caption = "정책별 감정 극성 100% 누적 막대"
    if missing:
        caption += f" ({'·'.join(missing)} 시기는 감정 데이터가 없어 제외)"
    st.caption(caption)

    fig_s = go.Figure()
    for grp, color in zip(sentiment.GROUP_ORDER, [theme.COLOR["sentiment_pos"], theme.COLOR["sentiment_neu"], theme.COLOR["sentiment_neg"]]):
        sub = ratio[ratio["감정그룹"] == grp].set_index("정책").reindex(policies)
        fig_s.add_trace(go.Bar(x=policies, y=sub["비율"], name=grp, marker_color=color))
    fig_s.update_layout(**theme.plotly_layout(height=340, barmode="stack", bargap=0.55))
>>>>>>> Stashed changes
    fig_s.update_yaxes(tickformat=".0%")
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        theme.plotly_chart(fig_s)
