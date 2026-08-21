"""지역별 변동률 — 상승:하락 자치구 수, 최대 상승/하락 자치구."""
import streamlit as st


def render(valid):
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
