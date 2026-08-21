"""2. 지역별 변동률 — 25개 자치구·법정동 단위 상승·하락 순위.

각 섹션의 실제 렌더링 코드는 sections/region/ 아래 파일로 나눠져 있다.
"""
import streamlit as st

from lib import load, metrics, theme
from sections.region import amount_band, dong_tables, kpi, ranking_chart, sidebar, tilemap

theme.inject_css()
theme.render_logo()
load.guard_apt_or_stop()

st.title("지역별 평단가 변동률")
st.caption("25개 자치구 · 법정동 단위 상승·하락 순위")

unit, sort_key, min_sample, region_filter, exclude_outlier = sidebar.render_sidebar()

apt = load.load_apt_master(exclude_outlier=exclude_outlier)
if region_filter:
    allowed_gu = [gu for r in region_filter for gu in theme.REGION_GROUPS[r]]
    apt = apt[apt["구"].isin(allowed_gu)]

gu_table = metrics.gu_change_table(apt)
valid = gu_table.dropna(subset=["평단가_변동률"])

kpi.render(valid)
st.divider()

ranking_chart.render(apt, gu_table, valid, unit, sort_key, min_sample)
st.divider()

col_e, col_f = st.columns(2)
with col_e:
    tilemap.render(apt, valid, unit, min_sample)
with col_f:
    amount_band.render(apt)
st.divider()

dong_tables.render(apt, min_sample, unit)
