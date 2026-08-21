"""3. 정책 전·후 비교 — 동일 기간 A/B 대조군으로 본 가격·거래량 변화."""
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from lib import load, metrics, theme

st.set_page_config(page_title="정책 전·후 비교 · 맛동산", page_icon="🏠", layout="wide")
theme.inject_css()
theme.render_logo()

if load.data_files_missing():
    st.error("data/ 폴더에 필요한 CSV가 없습니다. 메인 화면에서 안내를 확인해 주세요.")
    st.stop()

st.title("정책 전 · 후 비교")
st.caption("동일 기간 A/B 대조군으로 본 가격·거래량 변화")

apt_all = load.load_apt_master()
gu_list = sorted(apt_all["구"].unique())

with st.sidebar:
    base_gu = st.selectbox("기준 자치구", gu_list, index=gu_list.index("성동구") if "성동구" in gu_list else 0)
    dong_options = sorted(apt_all.loc[apt_all["구"] == base_gu, "법정동"].unique())
    selected_dong = st.multiselect("법정동 선택", dong_options, default=dong_options[: min(2, len(dong_options))])
    compare_metric = st.radio("비교 지표", ["평단가", "거래량", "금액대"])
    size_band = st.selectbox("전용면적", ["전체 (소형·중형·대형)", "소형", "중형", "대형"])
    normalize = st.checkbox("동일 기간 정규화 (417일)", value=True)
    exclude_outlier = st.checkbox("이상치 거래 제외", value=True)

apt = load.load_apt_master(exclude_outlier=exclude_outlier)
if size_band != "전체 (소형·중형·대형)":
    band_range = {"소형": (0, 60), "중형": (60, 100), "대형": (100, 10_000)}[size_band]
    apt = apt[(apt["전용면적"] >= band_range[0]) & (apt["전용면적"] < band_range[1])]

target = apt[apt["구"] == base_gu]
if selected_dong:
    target = target[target["법정동"].isin(selected_dong)]

before = target[target["정책여부"] == "정책전"]
after = target[target["정책여부"] == "정책후"]

# ---------------------------------------------------------------- 선택 지역 배너
period_note = " · 동일 기간 정규화 (417일)" if normalize else ""
st.info(
    f"**선택 지역** 서울특별시 {base_gu}"
    + (f" ({', '.join(selected_dong)})" if selected_dong else "")
    + f"  |  정책 전 2024-05-07 – 2025-06-27, 정책 후 2025-06-28 – 2026-08-18{period_note}  |  "
    + f"거래 {len(before):,}건 → {len(after):,}건"
)

st.divider()

# ---------------------------------------------------------------- KPI 4개
summary = metrics.policy_period_compare(apt, gu=base_gu, dong=selected_dong or None)
k1, k2, k3, k4 = st.columns(4)
k1.metric("평균 평단가 (만원/평)", f"{summary['avg_before']:,.0f} → {summary['avg_after']:,.0f}", f"{summary['price_rate']:+.1%}" if summary["price_rate"] is not None else "N/A")
k2.metric("거래 건수 (건)", f"{summary['count_before']:,.0f} → {summary['count_after']:,.0f}", f"{summary['count_rate']:+.1%}" if summary["count_rate"] is not None else "N/A")
area_before, area_after = before["전용면적"].mean(), after["전용면적"].mean()
k3.metric("평균 전용면적 (㎡)", f"{area_before:,.1f} → {area_after:,.1f}" if len(before) and len(after) else "N/A")

gu_rank_table = metrics.gu_change_table(apt).dropna(subset=["평단가_변동률"]).reset_index(drop=True)
gu_rank_table["순위"] = gu_rank_table["평단가_변동률"].rank(ascending=False, method="min").astype(int)
rank_row = gu_rank_table[gu_rank_table["구"] == base_gu]
rank_text = f"{int(rank_row['순위'].iloc[0])} / {len(gu_rank_table)}" if len(rank_row) else "N/A"
k4.metric("자치구 상승률 순위", rank_text)

if summary["low_sample"]:
    st.caption(f"⚠️ 정책 전·후 거래건수가 {metrics.MIN_SAMPLE}건 미만이라 평균이 흔들릴 수 있습니다.")

st.divider()

# ---------------------------------------------------------------- 월별 평단가·거래량
st.subheader(f"{base_gu} 월별 평단가 · 거래량")
st.caption("위 = 평균 평단가(만원/평), 아래 = 월 거래건수")
monthly = metrics.monthly_trend(target) if len(target) else metrics.monthly_trend(apt.iloc[0:0])
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.06)
fig.add_trace(go.Scatter(x=monthly["계약연월"], y=monthly["평단가"], mode="lines+markers", line=dict(color=theme.COLOR["policy_after"], width=3), name="평단가"), row=1, col=1)
fig.add_trace(go.Bar(x=monthly["계약연월"], y=monthly["거래건수"], marker_color=theme.COLOR["policy_before"], name="거래건수"), row=2, col=1)
fig.add_vline(x="2025-06", line_dash="dash", line_color=theme.COLOR["brand"], row=1, col=1)
fig.add_annotation(x="2025-06", y=1, yref="paper", text="2025-06-28 정책 시행", showarrow=False, yshift=10, font=dict(size=11, color=theme.COLOR["brand"]))
fig.update_layout(**theme.plotly_layout(height=440, showlegend=False))
st.plotly_chart(fig, use_container_width=True)

if len(before) and len(after):
    st.caption(
        f"평단가는 정책 이후 {before['평단가'].mean():,.0f} → {after['평단가'].mean():,.0f}만원/평으로 변했고, "
        f"거래건수는 {len(before):,}건 → {len(after):,}건으로 변했습니다."
    )

st.divider()

# ---------------------------------------------------------------- 지표 요약표
st.subheader("지표 요약표")
summary_rows = [
    ("평단가 (정책 전)", f"{before['평단가'].mean():,.0f} 만원/평" if len(before) else "N/A"),
    ("평단가 (정책 후)", f"{after['평단가'].mean():,.0f} 만원/평" if len(after) else "N/A"),
    ("평단가 변동률", f"{summary['price_rate']:+.1%}" if summary["price_rate"] is not None else "N/A"),
    ("거래건수 (정책 전)", f"{len(before):,} 건"),
    ("거래건수 (정책 후)", f"{len(after):,} 건"),
    ("거래량 변동률", f"{summary['count_rate']:+.1%}" if summary["count_rate"] is not None else "N/A"),
    ("평균 전용면적 (정책 전)", f"{area_before:,.1f} ㎡" if len(before) else "N/A"),
    ("평균 전용면적 (정책 후)", f"{area_after:,.1f} ㎡" if len(after) else "N/A"),
]
st.dataframe(
    {"지표": [r[0] for r in summary_rows], "값": [r[1] for r in summary_rows]},
    hide_index=True, use_container_width=True,
)

st.divider()

# ---------------------------------------------------------------- 전용면적별 비교 (비교 지표에 따라 전환)
def _area_bin(a: float) -> str:
    if a < 60:
        return "소형 (60㎡ 미만)"
    if a < 100:
        return "중형 (60~100㎡)"
    return "대형 (100㎡ 이상)"


if len(target):
    tmp = target.copy()
    tmp["면적구분"] = tmp["전용면적"].map(_area_bin)
    AREA_ORDER = ["소형 (60㎡ 미만)", "중형 (60~100㎡)", "대형 (100㎡ 이상)"]

    if compare_metric == "금액대":
        st.subheader("금액대별 거래 비중 변화")
        band_before = metrics.amount_band_distribution(before) if len(before) else None
        band_after = metrics.amount_band_distribution(after) if len(after) else None
        fig_area = go.Figure()
        if band_before is not None:
            fig_area.add_trace(go.Bar(x=band_before["금액대"], y=band_before["비율"], name="정책 전", marker_color=theme.COLOR["policy_before"]))
        if band_after is not None:
            fig_area.add_trace(go.Bar(x=band_after["금액대"], y=band_after["비율"], name="정책 후", marker_color=theme.COLOR["policy_after"]))
        fig_area.update_layout(**theme.plotly_layout(height=360, barmode="group"))
        fig_area.update_yaxes(tickformat=".0%")
    elif compare_metric == "평단가":
        st.subheader("전용면적별 평단가 변화")
        area_price = tmp.groupby(["면적구분", "정책여부"])["평단가"].mean().unstack(fill_value=None).reindex(AREA_ORDER)
        fig_area = go.Figure()
        fig_area.add_trace(go.Bar(x=area_price.index, y=area_price.get("정책전"), name="정책 전", marker_color=theme.COLOR["policy_before"]))
        fig_area.add_trace(go.Bar(x=area_price.index, y=area_price.get("정책후"), name="정책 후", marker_color=theme.COLOR["policy_after"]))
        fig_area.update_layout(**theme.plotly_layout(height=360, barmode="group", yaxis_title="만원/평"))
    else:
        st.subheader("전용면적별 거래량 변화")
        area_counts = tmp.groupby(["면적구분", "정책여부"]).size().unstack(fill_value=0).reindex(AREA_ORDER)
        fig_area = go.Figure()
        fig_area.add_trace(go.Bar(x=area_counts.index, y=area_counts.get("정책전"), name="정책 전", marker_color=theme.COLOR["policy_before"]))
        fig_area.add_trace(go.Bar(x=area_counts.index, y=area_counts.get("정책후"), name="정책 후", marker_color=theme.COLOR["policy_after"]))
        fig_area.update_layout(**theme.plotly_layout(height=360, barmode="group"))

    st.plotly_chart(fig_area, use_container_width=True)
else:
    st.info("선택한 조건에 해당하는 거래가 없습니다.")

st.divider()

# ---------------------------------------------------------------- 법정동 변동률 + 상세표
st.subheader(f"{base_gu} 법정동별 변동률")
dong_table = metrics.dong_change_table(apt[apt["구"] == base_gu], min_sample=10)
if len(dong_table):
    fig_dong = go.Figure(go.Bar(
        y=dong_table["법정동"], x=dong_table["변동률"], orientation="h",
        marker_color=[theme.COLOR["up"] if v > 0 else theme.COLOR["down"] for v in dong_table["변동률"]],
    ))
    fig_dong.update_layout(**theme.plotly_layout(height=max(280, 28 * len(dong_table)), showlegend=False, xaxis_title="평단가 변동률"))
    fig_dong.update_xaxes(tickformat=".0%")
    st.plotly_chart(fig_dong, use_container_width=True)
    st.dataframe(
        dong_table.assign(변동률=lambda d: d["변동률"].map(lambda v: f"{v:+.1%}"), 거래량_변동률=lambda d: d["거래량_변동률"].map(lambda v: f"{v:+.1%}" if v is not None else "N/A")),
        hide_index=True, use_container_width=True,
    )
else:
    st.info(f"{base_gu}에는 정책 전·후 각 10건 이상 거래된 법정동이 없습니다.")
