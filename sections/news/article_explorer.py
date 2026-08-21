"""뉴스·여론 분석 — 감정별 기사 탐색 표 (README 코드 예시 그대로)."""
import streamlit as st

from lib import sentiment


def render(news):
    st.subheader("감정별 기사 탐색")
    st.caption("막대 클릭 대신 감정 탭 + 표로 확인합니다.")

    emo = st.segmented_control("감정", ["전체"] + sentiment.EMOTIONS_7, default="전체")
    order = st.radio("정렬", ["확률 높은 순", "최신순"], horizontal=True, label_visibility="collapsed")

    view = news if emo in (None, "전체") else news[news["감정"] == emo]
    view = view.sort_values("수치", ascending=False) if order == "확률 높은 순" else view.sort_values("날짜", ascending=False)

    if st.button("랜덤 5건 뽑기"):
        view = view.sample(min(5, len(view))) if len(view) else view

    display_cols = ["감정", "기사제목", "정책", "단계", "날짜", "수치", "url"]
    st.dataframe(
        view[display_cols] if len(view) else view.reindex(columns=display_cols),
        column_config={
            "url": st.column_config.LinkColumn("원문", display_text="원문 ↗"),
            "수치": st.column_config.NumberColumn("확률", format="%.3f"),
            "날짜": st.column_config.DateColumn("날짜", format="YYYY-MM-DD"),
        },
        hide_index=True, use_container_width=True,
    )
    st.caption(f"조건에 맞는 기사 {len(view):,}건")
