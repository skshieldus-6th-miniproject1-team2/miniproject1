"""뉴스·여론 분석 — 정책별 감정 극성 100% 누적 막대 (구 '정부별 감정 극성').

실제 데이터에는 정부 비교 대신 정책(6·27/9·7/10·15) × 관점(기업/소비자/시장) × 전/후 축이 있다.
차트 형태(100% 누적 막대)는 그대로 두고, 관점·전후는 이 섹션 안에서 로컬로 고른다.
"""
import plotly.express as px
import streamlit as st

from lib import sentiment, theme
from sections.news.constants import PERSPECTIVE_OPTIONS

POLICY_ORDER = ["6·27", "9·7", "10·15"]
PERIOD_LABELS = {"before": "정책 시행 전", "after": "정책 시행 후"}


def render(perspective_summary):
    st.subheader("정책별 감정 극성")

    c1, c2 = st.columns(2)
    with c1:
        perspective = st.radio("관점", PERSPECTIVE_OPTIONS, horizontal=True)
    with c2:
        period_label = st.radio("시점", list(PERIOD_LABELS.values()), horizontal=True, index=1)
    period = next(k for k, v in PERIOD_LABELS.items() if v == period_label)

    df = perspective_summary[(perspective_summary["관점"] == perspective) & (perspective_summary["period"] == period)]
    long = df.melt(id_vars=["대책"], value_vars=sentiment.GROUP_ORDER, var_name="감정그룹", value_name="비율")

    fig = px.bar(
        long, x="대책", y="비율", color="감정그룹", barmode="stack",
        category_orders={"대책": POLICY_ORDER, "감정그룹": sentiment.GROUP_ORDER},
        color_discrete_map={"긍정": theme.COLOR["sentiment_pos"], "중립": theme.COLOR["sentiment_neu"], "부정": theme.COLOR["sentiment_neg"]},
    )
    fig.update_layout(**theme.plotly_layout(height=300, bargap=0.3))
    fig.update_yaxes(tickformat=".0%")
    theme.plotly_chart(fig)
