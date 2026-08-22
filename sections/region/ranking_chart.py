"""지역별 변동률 — 25개 자치구/법정동 다이버징 랭킹 막대."""
import plotly.graph_objects as go
import streamlit as st

from lib import metrics, theme


def render(apt, gu_table, valid, unit, sort_key, min_sample):
    if unit == "자치구":
        st.subheader("25개 자치구별 산술평균 평당가 변동률(%) 랭킹")
        level_df = valid.rename(columns={"구": "지역"})
    else:
        st.subheader("법정동별 산술평균 평당가 변동률(%) 랭킹")
        level_df = metrics.dong_change_table(apt, min_sample=min_sample)
        level_df["지역"] = level_df["구"] + " " + level_df["법정동"]
    st.caption(f"막대 = 산술평균 평단가 변동률(%) · {min_sample}건 미만 지역은 제외")

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
    plot_df["_pct"] = plot_df[rate_col] * 100  # % 단위 숫자 그대로 표시 (틱에 % 기호 없이)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=plot_df["지역"], x=plot_df["_pct"], orientation="h",
        marker_color=[theme.COLOR["up"] if v > 0 else theme.COLOR["down"] for v in plot_df[rate_col]],
    ))
    # 25개 자치구 막대가 세로로 빽빽했던 문제: 막대당 높이를 22px→34px로 늘려 전체 차트 높이를 키움
    fig.update_layout(**theme.plotly_layout(height=max(420, 34 * len(plot_df)), showlegend=False, xaxis_title="산술평균 평당가 변동률(%)"))
    fig.update_xaxes(zeroline=True, zerolinecolor=theme.COLOR["text_faint"], zerolinewidth=1)
    fig.update_yaxes(autorange="reversed")  # 위에서 아래로 변동률 오름차순(가장 낮은 값이 맨 위)이 되도록
    theme.plotly_chart(fig)

    if unit == "자치구":
        low_sample_gu = gu_table[gu_table["표본부족"]]["구"].tolist()
        if low_sample_gu:
            st.caption(f"표본 부족(정책 전·후 각 {metrics.MIN_SAMPLE}건 미만)으로 제외: {', '.join(low_sample_gu)}")
