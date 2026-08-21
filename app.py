"""1. 메인 대시보드 — 정책 시행 전·후 서울 아파트 시장과 여론을 한 화면에 요약한다.

각 섹션의 실제 렌더링 코드는 sections/main/ 아래 파일로 나눠져 있다.
이 파일은 데이터를 준비해서 순서대로 넘겨주는 얇은 진입점이다.
"""
import streamlit as st

from lib import load, metrics, theme
from sections.main import kpi, monthly_trend, news_phase, public_reaction, quadrant, region_comparison, sidebar

st.set_page_config(page_title="맛동산", page_icon="🏠", layout="wide")


def render_main_dashboard():
    theme.inject_css()
    theme.render_logo()
    load.guard_or_stop()

    st.title("서울 아파트 정책 분석")
    st.caption("정책 시행 전·후 서울 아파트 시장과 여론 — 한 화면 요약")

    period, shown_markers, region_mode, exclude_outlier, exclude_unsettled = sidebar.render_sidebar()

    apt = load.load_apt_master(exclude_outlier=exclude_outlier, exclude_unsettled_month=exclude_unsettled)
    if period == "정책 전":
        apt_view = apt[apt["정책여부"] == "정책전"]
    elif period == "정책 후":
        apt_view = apt[apt["정책여부"] == "정책후"]
    else:
        apt_view = apt

    news = load.load_news("category")
    gu_table = metrics.gu_change_table(apt)

    kpi.render(apt, gu_table, news)
    st.divider()

    monthly_trend.render(apt_view, shown_markers)
    st.divider()

    col_a, col_b = st.columns([3, 2])
    with col_a:
        quadrant.render(apt)
    with col_b:
        region_comparison.render(apt, gu_table, region_mode)
    st.divider()

    col_c, col_d = st.columns(2)
    with col_c:
        public_reaction.render(news)
    with col_d:
        news_phase.render(news)

    st.caption("데이터: apt_master.csv, news_titles_category.csv — 현재는 화면 검증용 임시(mock) 데이터입니다.")


# st.navigation()으로 좌측 네비게이션 라벨을 명시적으로 지정한다.
# (pages/ 자동 인식 방식은 진입 파일 이름을 그대로 라벨로 써서 "app"으로 보였다.)
pg = st.navigation([
    st.Page(render_main_dashboard, title="메인 대시보드", icon="🏠", default=True),
    st.Page("pages/1_지역별_변동률.py", title="지역별 변동률", icon="🗺️"),
    st.Page("pages/2_정책_전후_비교.py", title="정책 전후 비교", icon="📊"),
    st.Page("pages/3_뉴스_여론_분석.py", title="뉴스·여론 분석", icon="📰"),
])
pg.run()
