"""1. 메인 대시보드 — 정책 시행 전·후 서울 아파트 시장과 여론을 한 화면에 요약한다."""
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from lib import load, metrics, sentiment, theme

st.set_page_config(page_title="맛동산 · 서울 아파트 정책 분석", page_icon="🏠", layout="wide")
theme.inject_css()
theme.render_logo()

missing = load.data_files_missing()
if missing:
    st.error(
        "data/ 폴더에 다음 파일이 없어 화면을 채울 수 없습니다: "
        + ", ".join(missing)
        + "\n\n실제 파이프라인 산출물이 올라오기 전까지는 임시(mock) 데이터로 확인해 주세요."
    )
    st.stop()

st.title("맛동산 🍡 서울 아파트 정책 분석")
st.caption("정책 시행 전·후 서울 아파트 시장과 여론 — 한 화면 요약")

# ---------------------------------------------------------------- 사이드바
with st.sidebar:
    st.markdown("### 분석 구간")
    period = st.radio("분석 구간", ["정책 전", "정책 후", "전체"], index=2, label_visibility="collapsed")

    st.markdown("### 표시 정책 마커")
    marker_cols = st.columns(2)
    shown_markers = []
    for i, (label, date) in enumerate(theme.POLICY_MARKERS.items()):
        with marker_cols[i % 2]:
            if st.checkbox(label, value=True, key=f"marker_{label}"):
                shown_markers.append((label, date))

    st.markdown("### 권역 구분")
    region_mode = st.radio("권역 구분", ["4대 권역", "25개 구"], label_visibility="collapsed")

    st.markdown("### ")
    exclude_outlier = st.checkbox("이상치 거래 제외", value=True)
    exclude_unsettled = st.checkbox("미집계 월 제외 (2026-08)", value=True)

apt = load.load_apt_master(exclude_outlier=exclude_outlier, exclude_unsettled_month=exclude_unsettled)
if period == "정책 전":
    apt_view = apt[apt["정책여부"] == "정책전"]
elif period == "정책 후":
    apt_view = apt[apt["정책여부"] == "정책후"]
else:
    apt_view = apt

news = load.load_news("category")

# ---------------------------------------------------------------- KPI
gu_table = metrics.gu_change_table(apt)
overall_before = apt[apt["정책여부"] == "정책전"]["평단가"].mean()
overall_after = apt[apt["정책여부"] == "정책후"]["평단가"].mean()
overall_rate = metrics.change_rate(overall_before, overall_after)
count_before, count_after = (apt["정책여부"] == "정책전").sum(), (apt["정책여부"] == "정책후").sum()
count_rate = metrics.change_rate(count_before, count_after)
up_gu = int((gu_table["평단가_변동률"] > 0).sum())
total_gu = int(gu_table["평단가_변동률"].notna().sum())
group_counts = sentiment.add_group_column(news)["감정그룹"].value_counts()
neg_pct_overall = group_counts.get("부정", 0) / group_counts.sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("서울 평균 평단가 (정책 후)", f"{overall_after:,.0f} 만원/평", f"{overall_rate:+.1%}")
k2.metric("전체 거래 건수", f"{count_after:,.0f} 건", f"{count_rate:+.1%}")
k3.metric("상승 자치구 수", f"{up_gu} / {total_gu}")
k4.metric("뉴스 부정 감정 비중", f"{neg_pct_overall:.1%}")

st.divider()

# ---------------------------------------------------------------- 월별 평단가 + 거래량
st.subheader("월별 서울 평균 평단가와 거래량")
st.caption("위 = 산술평균 평단가(만원/평), 아래 = 월 거래건수 · 같은 x축을 공유하되 축은 겹치지 않는다")

monthly = metrics.monthly_trend(apt_view)
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.06)
fig.add_trace(
    go.Scatter(x=monthly["계약연월"], y=monthly["평단가"], mode="lines", line=dict(color=theme.COLOR["brand"], width=3), name="평단가"),
    row=1, col=1,
)
fig.add_trace(
    go.Bar(x=monthly["계약연월"], y=monthly["거래건수"], marker_color=theme.COLOR["policy_before"], name="거래건수"),
    row=2, col=1,
)
visible_markers = [(label, date) for label, date in shown_markers if monthly["계약연월"].min() <= date[:7] <= monthly["계약연월"].max()]
for i, (label, date) in enumerate(visible_markers):
    fig.add_vline(x=date[:7], line_dash="dash", line_color=theme.COLOR["text_faint"], row=1, col=1)
    # 인접한 정책 마커끼리 라벨이 겹치지 않도록 위아래로 번갈아 배치한다
    fig.add_annotation(x=date[:7], y=1, yref="paper", text=label, showarrow=False, yshift=10 + (i % 2) * 16, font=dict(size=10, color=theme.COLOR["text_muted"]))
fig.update_layout(**theme.plotly_layout(height=460, showlegend=False))
fig.update_yaxes(title_text="만원/평", row=1, col=1)
fig.update_yaxes(title_text="거래건수", row=2, col=1)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------- 4분면 매트릭스
col_a, col_b = st.columns([3, 2])
with col_a:
    st.subheader("거래량은 줄었는데 평단가는 올랐다")
    st.caption("자치구별 거래량 증감률(x) × 평단가 변동률(y) · 색 = 권역 · 음영 = 거래량↓·가격↑ 사분면")
    quad = metrics.quadrant_data(apt)
    top_left_n = int(((quad["거래량_변동률"] < 0) & (quad["평단가_변동률"] > 0)).sum())
    fig_q = go.Figure()
    for region, g in quad.groupby("권역"):
        fig_q.add_trace(
            go.Scatter(
                x=g["거래량_변동률"], y=g["평단가_변동률"], mode="markers+text",
                text=g["구"], textposition="top center", textfont=dict(size=10),
                marker=dict(size=11, color=theme.REGION_COLOR.get(region, theme.SERIES_OTHER)),
                name=region,
            )
        )
    fig_q.add_hline(y=0, line_color=theme.COLOR["border"])
    fig_q.add_vline(x=0, line_color=theme.COLOR["border"])
    x_min, x_max = quad["거래량_변동률"].min(), 0
    y_min, y_max = 0, quad["평단가_변동률"].max()
    fig_q.add_shape(type="rect", x0=x_min * 1.1, x1=0, y0=0, y1=y_max * 1.1, fillcolor=theme.COLOR["sentiment_neg"], opacity=0.06, line_width=0)
    fig_q.add_annotation(x=x_min * 1.05, y=y_max * 1.05, text=f"거래량↓·평단가↑ {top_left_n}곳", showarrow=False, font=dict(size=11, color=theme.COLOR["down"]), xanchor="left")
    fig_q.update_layout(**theme.plotly_layout(height=480, xaxis_title="거래량 증감률", yaxis_title="평단가 변동률"))
    fig_q.update_xaxes(tickformat=".0%")
    fig_q.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_q, use_container_width=True)

with col_b:
    if region_mode == "4대 권역":
        st.subheader("4대 권역 비교")
        compare_df = metrics.region_summary(apt).rename(columns={"권역": "구분"})
    else:
        st.subheader("25개 구 비교")
        compare_df = gu_table.rename(columns={"구": "구분"}).sort_values("평단가_변동률", ascending=True)

    fig_r = go.Figure()
    fig_r.add_trace(go.Bar(
        y=compare_df["구분"], x=compare_df["평단가_변동률"], orientation="h", name="평단가 변동률",
        marker_color=[theme.COLOR["up"] if v and v > 0 else theme.COLOR["down"] for v in compare_df["평단가_변동률"]],
    ))
    fig_r.update_layout(**theme.plotly_layout(height=230 if region_mode == "4대 권역" else 520, showlegend=False, title="평단가 변동률"))
    fig_r.update_xaxes(tickformat=".0%")
    st.plotly_chart(fig_r, use_container_width=True)

    if region_mode == "4대 권역":
        fig_v = go.Figure()
        fig_v.add_trace(go.Bar(
            y=compare_df["구분"], x=compare_df["거래량_변동률"], orientation="h", name="거래량 변동률",
            marker_color=[theme.COLOR["up"] if v and v > 0 else theme.COLOR["down"] for v in compare_df["거래량_변동률"]],
        ))
        fig_v.update_layout(**theme.plotly_layout(height=230, showlegend=False, title="거래량 변동률"))
        fig_v.update_xaxes(tickformat=".0%")
        st.plotly_chart(fig_v, use_container_width=True)

st.divider()

# ---------------------------------------------------------------- 대중 반응
col_c, col_d = st.columns(2)
with col_c:
    st.subheader("대중 반응")
    st.caption("4개 정부 감정 극성 100% 누적 막대")
    GOV_ORDER = ["박근혜", "문재인", "윤석열", "이재명"]
    ratio = sentiment.group_ratio(news, by=["정부"])
    fig_s = go.Figure()
    for grp, color in zip(sentiment.GROUP_ORDER, [theme.COLOR["sentiment_pos"], theme.COLOR["sentiment_neu"], theme.COLOR["sentiment_neg"]]):
        sub = ratio[ratio["감정그룹"] == grp].set_index("정부").reindex(GOV_ORDER)
        fig_s.add_trace(go.Bar(x=GOV_ORDER, y=sub["비율"], name=grp, marker_color=color))
    fig_s.update_layout(**theme.plotly_layout(height=340, barmode="stack"))
    fig_s.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_s, use_container_width=True)

with col_d:
    st.subheader("보도 시점 분포")
    st.caption("시행 전 / 발표 후·시행 전 / 시행 후 (잠정 — 뉴스 소스 확정 후 갱신 예정)")
    phase_map = {"시행 전": "시행 전", "시행일": "발표 후·시행 전", "초기 반응": "발표 후·시행 전", "체감 반응": "시행 후"}
    news_phase = news.copy()
    news_phase["3단계"] = news_phase["시기"].map(phase_map)
    counts = news_phase["3단계"].value_counts().reindex(["시행 전", "발표 후·시행 전", "시행 후"]).fillna(0)
    fig_p = go.Figure(go.Bar(x=counts.index, y=counts.values, marker_color=theme.COLOR["brand"]))
    fig_p.update_layout(**theme.plotly_layout(height=340, showlegend=False))
    st.plotly_chart(fig_p, use_container_width=True)

st.caption("데이터: apt_master.csv, news_titles_category.csv — 현재는 화면 검증용 임시(mock) 데이터입니다.")
