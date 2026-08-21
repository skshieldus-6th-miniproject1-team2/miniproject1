"""뉴스·여론 분석 — 기사 수집 구성 (카테고리 × 시점 교차 분류)."""
import streamlit as st


def render(news_all):
    st.subheader("기사 수집 구성")
    st.caption("네이버 뉴스 · 정책 카테고리 × 시점 교차 분류")

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
