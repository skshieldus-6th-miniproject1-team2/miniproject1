"""지역별 변동률 — 금액대별 거래 비중 도넛."""
import plotly.express as px
import streamlit as st

from lib import metrics, theme


def render(apt):
    st.subheader("금액대별 거래 비중")
    band = metrics.amount_band_distribution(apt)
    fig_band = px.pie(band, names="금액대", values="건수", hole=0.5, color_discrete_sequence=theme.SERIES)
    fig_band.update_layout(**theme.plotly_layout(height=420))
    theme.plotly_chart(fig_band)
