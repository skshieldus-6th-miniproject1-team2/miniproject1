"""지역별 변동률 — 대출 규제선 기준 가격대별 거래 비중 및 변동."""
import plotly.graph_objects as go
import streamlit as st

from lib import metrics, theme


def render(apt):
    st.subheader("대출 규제선 기준 가격대별 거래 비중")
    st.caption("막대 = 정책 전·후 거래 비중(%) · 라벨 = 비중 변동폭(%p)")

    before = metrics.amount_band_distribution(apt[apt["정책여부"] == "정책전"])
    after = metrics.amount_band_distribution(apt[apt["정책여부"] == "정책후"])
    labels = before["금액대"].tolist()
    before_pct = before["비율"] * 100
    after_pct = after.set_index("금액대").reindex(labels)["비율"] * 100
    delta = after_pct.to_numpy() - before_pct.to_numpy()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=before_pct, name="정책 시행 전", marker_color=theme.COLOR["policy_before"]))
    fig.add_trace(go.Bar(
        x=labels, y=after_pct, name="정책 시행 후", marker_color=theme.COLOR["policy_after"],
        text=[f"{d:+.1f}%p" for d in delta],
        textposition="outside",
        textfont=dict(color=[theme.COLOR["up"] if d > 0 else theme.COLOR["down"] for d in delta]),
    ))
    fig.update_layout(**theme.plotly_layout(height=420, barmode="group", yaxis_title="거래 비중(%)"))
    theme.plotly_chart(fig)
