"""뉴스·여론 분석 — 시점별 감정 분포 교차표."""
import streamlit as st

from lib import sentiment
from sections.news.constants import PHASE_OPTIONS


def render(news):
    st.subheader("시점별 감정 분포")
    st.caption("기사 수 · 현재 필터 기준")
<<<<<<< Updated upstream
    tab = news.groupby(["시기", "감정"]).size().unstack(fill_value=0).reindex(PHASE_OPTIONS).reindex(columns=sentiment.EMOTIONS_7, fill_value=0)
    st.dataframe(tab, use_container_width=False)
=======
    tab = news.groupby(["단계", "감정"]).size().unstack(fill_value=0).reindex(PHASE_OPTIONS).reindex(columns=sentiment.EMOTIONS_7, fill_value=0)

    # [수정 3] st.dataframe(인터랙티브 그리드)은 캔버스로 그려져서 폰트/패딩을 CSS로 줄일 수 없고,
    # 1/3 폭으로 좁히면 내부 가로 스크롤이 생긴다. pandas Styler로 만들어 st.table(정적 HTML 표)로
    # 렌더링하면 컨테이너 폭에 맞춰 자연스럽게 줄어들어 스크롤이 생기지 않는다. 데이터 값(tab)은
    # 그대로 두고 폰트 크기·셀 패딩만 촘촘하게 조정. EMOTIONS_7 라벨은 이미 전부 2글자라 축약 불필요.
    styler = tab.style.set_table_styles([
        {"selector": "th, td", "props": [("font-size", "11px"), ("padding", "2px 4px"), ("white-space", "nowrap")]},
        {"selector": "td", "props": [("text-align", "center")]},
    ])
    st.table(styler)
>>>>>>> Stashed changes
