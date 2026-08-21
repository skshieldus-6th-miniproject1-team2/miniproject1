<<<<<<< Updated upstream
"""뉴스·여론 분석 — 기사 수집 구성 (카테고리 × 시점 교차 분류)."""
import streamlit as st


def render(news_all):
=======
"""뉴스·여론 분석 — 기사 수집 구성 (정책별).

7종 감정 분석(News_Scraping_retouch.csv)은 2025-09-26까지만 돼 있어서, 그 이후에 시작하는
10·15 대책 기사가 감정 조인 결과에서 통째로 빠진다. 이 섹션은 수집량 자체를 보여주는
곳이라 감정 조인 없이 j_News_Scraping.csv(전체 수집분)를 그대로 쓴다.
"""
import plotly.express as px
import streamlit as st

from lib import theme
from sections.news.constants import POLICY_OPTIONS

# [수정 1] 진행바(st.progress) 대신 원형 그래프로 표현. 브랜드 주황(#EB6834)을 가장 진한 값으로
# 두고 옅어지는 순서로 4단계를 배치해 기존 톤을 유지 (건수가 큰 6·27이 가장 진하게 보임).
PIE_COLORS = ["#EB6834", "#F2905E", "#F7B686", "#FBD9BC"]


def render(news_full):
>>>>>>> Stashed changes
    st.subheader("기사 수집 구성")
    st.caption("네이버 뉴스 · 정책 카테고리 × 시점 교차 분류")

<<<<<<< Updated upstream
    category_options = sorted(news_all["카테고리"].unique())
    cat_counts = news_all["카테고리"].value_counts().reindex(category_options).fillna(0)
    for cat, count in cat_counts.items():
        ratio = count / len(news_all)
        st.markdown(f"**{cat}** &nbsp; {int(count)}건 · {ratio:.1%}")
        st.progress(ratio)

    pre_settle = news_all[news_all["시기"] != "체감 반응"]
    post_ratio = len(pre_settle) / len(news_all)
    st.caption(
        f"보도량은 발표 후 · 시행 전 구간에 {post_ratio:.0%}({len(pre_settle)}건) 몰립니다. "
        f"시행 후 기사는 {len(news_all) - len(pre_settle)}건뿐이라 \"시행 후 여론\"을 논할 때는 표본이 얇다는 점을 함께 밝혀야 한다."
    )
=======
    policy_counts = news_full["정책"].value_counts().reindex(POLICY_OPTIONS).fillna(0)
    plot_df = policy_counts.rename_axis("정책").reset_index(name="건수")
    plot_df["건수"] = plot_df["건수"].astype(int)

    fig = px.pie(
        plot_df, names="정책", values="건수", color="정책",
        category_orders={"정책": POLICY_OPTIONS},
        color_discrete_sequence=PIE_COLORS,
    )
    fig.update_traces(textinfo="label+value+percent", textposition="inside")
    fig.update_layout(**theme.plotly_layout(height=340, showlegend=False))
    theme.plotly_chart(fig, use_container_width=True)
>>>>>>> Stashed changes
