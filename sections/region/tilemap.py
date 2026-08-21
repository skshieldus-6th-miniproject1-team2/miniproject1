"""지역별 변동률 — 자치구/법정동 타일맵."""
import plotly.graph_objects as go
import streamlit as st

from lib import metrics, theme


def render(apt, valid, unit, min_sample):
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
    theme.plotly_chart(tile)
