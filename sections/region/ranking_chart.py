"""지역별 변동률 — 25개 자치구/법정동 다이버징 랭킹 막대."""
import plotly.graph_objects as go
import streamlit as st

from lib import metrics, theme


def render(apt, gu_table, valid, unit, sort_key, min_sample):
    if unit == "자치구":
        st.subheader("25개 자치구 평단가 변동률")
        level_df = valid.rename(columns={"구": "지역"})
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
