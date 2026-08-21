"""2. 지역별 변동률 — 25개 자치구·법정동 단위 상승·하락 순위."""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib import load, metrics, theme

st.set_page_config(page_title="지역별 변동률 · 맛동산", page_icon="🏠", layout="wide")
theme.inject_css()
theme.render_logo()

if load.data_files_missing():
    st.error("data/ 폴더에 필요한 CSV가 없습니다. 메인 화면에서 안내를 확인해 주세요.")
    st.stop()

st.title("지역별 평단가 변동률")
st.caption("25개 자치구 · 법정동 단위 상승·하락 순위")

with st.sidebar:
    unit = st.radio("집계 단위", ["자치구", "법정동"])
    sort_key = st.selectbox("정렬 기준", ["변동률 높은 순", "변동률 낮은 순", "거래건수 많은 순"])
    min_sample = st.slider("최소 거래건수 (동 단위 신뢰 구간)", min_value=10, max_value=100, value=30, step=5)
    st.caption(f"{min_sample}건 이상 (정책 전·후 각각 기준)")
    region_filter = st.multiselect("권역 필터", list(theme.REGION_GROUPS.keys()))
    exclude_outlier = st.checkbox("이상치 거래 제외", value=True)

apt = load.load_apt_master(exclude_outlier=exclude_outlier)
if region_filter:
    allowed_gu = [gu for r in region_filter for gu in theme.REGION_GROUPS[r]]
    apt = apt[apt["구"].isin(allowed_gu)]

gu_table = metrics.gu_change_table(apt)
valid = gu_table.dropna(subset=["평단가_변동률"])

k1, k2, k3 = st.columns(3)
up_n = int((valid["평단가_변동률"] > 0).sum())
down_n = int((valid["평단가_변동률"] < 0).sum())
k1.metric("상승 : 하락 자치구", f"{up_n} : {down_n}", f"25개 구 전체 · 중위 변동률 {valid['평단가_변동률'].median():+.1%}")

best = valid.sort_values("평단가_변동률", ascending=False).iloc[0] if len(valid) else None
if best is not None:
    k2.metric("최대 상승 자치구", best["구"], f"{best['평단가_변동률']:+.1%}")

worst = valid.sort_values("평단가_변동률", ascending=True).iloc[0] if len(valid) else None
if worst is not None:
    k3.metric("최대 하락 자치구", worst["구"], f"{worst['평단가_변동률']:+.1%}")

st.divider()

# ---------------------------------------------------------------- 다이버징 랭킹 (집계 단위에 따라 자치구/법정동)
if unit == "자치구":
    st.subheader("25개 자치구 평단가 변동률")
    level_df = valid.rename(columns={"구": "지역"})
    label_col = "거래량_변동률"
else:
    st.subheader("법정동 평단가 변동률")
    level_df = metrics.dong_change_table(apt, min_sample=min_sample)
    level_df["지역"] = level_df["구"] + " " + level_df["법정동"]
    label_col = "거래량_변동률"
st.caption(f"막대 = 평단가 변동률(%) · 라벨 = 같은 기간 거래량 변동률(%) · {min_sample}건 미만 지역은 제외")

sort_map = {
    "변동률 높은 순": ("평단가_변동률" if unit == "자치구" else "변동률", False),
    "변동률 낮은 순": ("평단가_변동률" if unit == "자치구" else "변동률", True),
    "거래건수 많은 순": ("거래건수_정책후" if unit == "자치구" else "거래건수", False),
}
sort_col, sort_ascending = sort_map[sort_key]
rate_col = "평단가_변동률" if unit == "자치구" else "변동률"
plot_df = level_df.sort_values(sort_col, ascending=sort_ascending)
if unit == "법정동" and len(plot_df) > 40:
    st.caption(f"표시 상한 40건 · 조건을 만족하는 법정동 {len(plot_df)}건 중 정렬 기준 상위 40건만 표시")
    plot_df = plot_df.head(40)
# 다이버징 바는 항상 값 오름차순으로 그려야 위에서 아래로 큰 값 -> 작은 값 순서로 보인다
plot_df = plot_df.sort_values(rate_col, ascending=True)

fig = go.Figure()
fig.add_trace(go.Bar(
    y=plot_df["지역"], x=plot_df[rate_col], orientation="h",
    marker_color=[theme.COLOR["up"] if v > 0 else theme.COLOR["down"] for v in plot_df[rate_col]],
    text=[f"{v:+.1%} (거래량 {r:+.1%})" for v, r in zip(plot_df[rate_col], plot_df[label_col])],
    textposition="outside",
    cliponaxis=False,  # 짧은 막대의 바깥 라벨이 플롯 경계에서 잘리지 않도록
))
fig.update_layout(**theme.plotly_layout(height=max(420, 22 * len(plot_df)), showlegend=False, xaxis_title="평단가 변동률"))
axis_lo = min(0, plot_df[rate_col].min())
axis_hi = max(0, plot_df[rate_col].max())
fig.update_xaxes(tickformat=".0%", range=[axis_lo * 1.6 if axis_lo < 0 else -0.01, axis_hi * 1.6 if axis_hi > 0 else 0.01])
st.plotly_chart(fig, use_container_width=True)

if unit == "자치구":
    low_sample_gu = gu_table[gu_table["표본부족"]]["구"].tolist()
    if low_sample_gu:
        st.caption(f"표본 부족(정책 전·후 각 {metrics.MIN_SAMPLE}건 미만)으로 제외: {', '.join(low_sample_gu)}")

st.divider()

col_e, col_f = st.columns(2)
with col_e:
    if unit == "자치구":
        st.subheader("자치구 타일맵")
        tile_labels, tile_values, tile_rates = valid["구"], valid["거래건수_정책후"].clip(lower=1), valid["평단가_변동률"]
    else:
        st.subheader("법정동 타일맵")
        dong_full = metrics.dong_change_table(apt, min_sample=min_sample)
        tile_labels = dong_full["구"] + " " + dong_full["법정동"]
        tile_values = dong_full["거래건수"].clip(lower=1)
        tile_rates = dong_full["변동률"]
    tile = go.Figure(go.Treemap(
        labels=tile_labels, parents=[""] * len(tile_labels), values=tile_values,
        marker=dict(colors=tile_rates, colorscale=[[0, theme.COLOR["down"]], [0.5, theme.COLOR["card"]], [1, theme.COLOR["up"]]], cmid=0),
        text=[f"{g}<br>{v:+.1%}" for g, v in zip(tile_labels, tile_rates)],
        textinfo="text",
    ))
    tile.update_layout(**theme.plotly_layout(height=420, margin=dict(l=0, r=0, t=10, b=0)))
    st.plotly_chart(tile, use_container_width=True)

with col_f:
    st.subheader("금액대별 거래 비중")
    band = metrics.amount_band_distribution(apt)
    fig_band = px.pie(band, names="금액대", values="건수", hole=0.5, color_discrete_sequence=theme.SERIES)
    fig_band.update_layout(**theme.plotly_layout(height=420))
    st.plotly_chart(fig_band, use_container_width=True)

st.divider()

st.subheader("법정동 변동률 TOP 10 / 하위 10")
top10, bottom10 = metrics.dong_ranking(apt, top_n=10, min_sample=min_sample)
col_g, col_h = st.columns(2)
with col_g:
    st.markdown("**상승 TOP 10**")
    st.dataframe(
        top10.assign(변동률=lambda d: d["변동률"].map(lambda v: f"{v:+.1%}")),
        hide_index=True, use_container_width=True,
    )
with col_h:
    st.markdown("**하위 10**")
    st.dataframe(
        bottom10.assign(변동률=lambda d: d["변동률"].map(lambda v: f"{v:+.1%}")),
        hide_index=True, use_container_width=True,
    )

if unit == "법정동" and (top10.empty and bottom10.empty):
    st.info(f"최소 거래건수 {min_sample}건을 만족하는 법정동이 없습니다. 슬라이더 값을 낮춰보세요.")
