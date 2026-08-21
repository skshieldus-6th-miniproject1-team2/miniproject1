"""3. 정책 전·후 비교 — 동일 기간 A/B 대조군으로 본 가격·거래량 변화.

각 섹션의 실제 렌더링 코드는 sections/policy_compare/ 아래 파일로 나눠져 있다.
"""
import streamlit as st

from lib import load, metrics, theme
from sections.policy_compare import area_compare, banner, dong_compare, kpi, monthly_chart, sidebar, summary_table

theme.inject_css()
theme.render_logo()
load.guard_apt_or_stop()

st.title("정책 전 · 후 비교")
st.caption("동일 기간 A/B 대조군으로 본 가격·거래량 변화")

apt_all = load.load_apt_master()
base_gu, selected_dong, compare_metric, size_band, normalize, exclude_outlier = sidebar.render_sidebar(apt_all)

apt = load.load_apt_master(exclude_outlier=exclude_outlier)
if size_band != "전체 (소형·중형·대형)":
    band_range = {"소형": (0, 60), "중형": (60, 100), "대형": (100, 10_000)}[size_band]
    apt = apt[(apt["전용면적"] >= band_range[0]) & (apt["전용면적"] < band_range[1])]

target = apt[apt["구"] == base_gu]
if selected_dong:
    target = target[target["법정동"].isin(selected_dong)]

before = target[target["정책여부"] == "정책전"]
after = target[target["정책여부"] == "정책후"]
area_before, area_after = before["전용면적"].mean(), after["전용면적"].mean()

banner.render(base_gu, selected_dong, normalize, before, after)
st.divider()

summary = metrics.policy_period_compare(apt, gu=base_gu, dong=selected_dong or None)
kpi.render(apt, base_gu, summary, before, after, area_before, area_after)
st.divider()

monthly_chart.render(base_gu, target, apt, before, after)
st.divider()

col_summary, col_area = st.columns([2, 3])
with col_summary:
    summary_table.render(before, after, summary, area_before, area_after)
with col_area:
    area_compare.render(target, before, after, compare_metric)
st.divider()

dong_compare.render(apt, base_gu)
