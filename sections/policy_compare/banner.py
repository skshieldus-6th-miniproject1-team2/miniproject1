"""정책 전·후 비교 — 선택 지역·기간 배너."""
import streamlit as st


def render(base_gu, selected_dong, normalize, before, after):
    period_note = " · 동일 기간 정규화 (417일)" if normalize else ""
    st.info(
        f"**선택 지역** 서울특별시 {base_gu}"
        + (f" ({', '.join(selected_dong)})" if selected_dong else "")
        + f"  |  정책 전 2024-05-07 – 2025-06-27, 정책 후 2025-06-28 – 2026-08-18{period_note}  |  "
        + f"거래 {len(before):,}건 → {len(after):,}건"
    )
