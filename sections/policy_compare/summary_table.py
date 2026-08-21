"""정책 전·후 비교 — 지표 요약표 (8행)."""
import streamlit as st


def render(before, after, summary, area_before, area_after):
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
