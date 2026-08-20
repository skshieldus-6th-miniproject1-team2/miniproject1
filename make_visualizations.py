"""
서울 아파트 정책 시행 전후 시장 변화 시각화 세트

processed/apt_master.csv 등 전처리 결과물과 seoul_raw_data/ 원본을 이용해
6개의 png 차트를 visualizations/ 폴더에 생성한다.

사용법:
    python make_visualizations.py
"""

from __future__ import annotations

import glob
import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Polygon

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

PROCESSED_DIR = "processed"
RAW_DIR = "seoul_raw_data"
OUT_DIR = "visualizations"
POLICY_DATE = pd.Timestamp("2025-06-28")

PRE, POST = "정책전", "정책후"
COLOR_PRE, COLOR_POST = "#4C72B0", "#DD8452"

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 110


def _savefig(fig, filename: str) -> None:
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[저장] {path}")


# ---------------------------------------------------------------------------
# 1. 정책전/후 평단가 분포 히스토그램 (오버레이, x축 로그스케일)
# ---------------------------------------------------------------------------

def chart1_price_distribution(master: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5))

    bins = np.logspace(
        np.log10(master["평단가"].clip(lower=1).min()),
        np.log10(master["평단가"].max()),
        60,
    )

    for policy, color in [(PRE, COLOR_PRE), (POST, COLOR_POST)]:
        vals = master.loc[master["정책여부"] == policy, "평단가"]
        ax.hist(
            vals, bins=bins, density=True, alpha=0.55,
            color=color, label=f"{policy} (n={len(vals):,})",
        )

    ax.set_xscale("log")
    ax.set_xlabel("평단가 (만원/평, 로그스케일)")
    ax.set_ylabel("밀도")
    ax.set_title("정책 시행 전후 평단가 분포 (오버레이 히스토그램)")
    ax.legend()
    fig.tight_layout()
    _savefig(fig, "1_평단가분포_히스토그램.png")

    pre_mean = master.loc[master["정책여부"] == PRE, "평단가"].mean()
    post_mean = master.loc[master["정책여부"] == POST, "평단가"].mean()
    pre_med = master.loc[master["정책여부"] == PRE, "평단가"].median()
    post_med = master.loc[master["정책여부"] == POST, "평단가"].median()
    print(
        f"  -> 평균 평단가 {pre_mean:,.0f} -> {post_mean:,.0f} "
        f"({(post_mean/pre_mean-1)*100:+.1f}%), "
        f"중위값 {pre_med:,.0f} -> {post_med:,.0f} "
        f"({(post_med/pre_med-1)*100:+.1f}%)"
    )


# ---------------------------------------------------------------------------
# 2. 사가정센트럴아이파크 시계열 라인차트
# ---------------------------------------------------------------------------

def chart2_sagajeong_timeseries(master: pd.DataFrame) -> None:
    sub = master[
        (master["구"] == "중랑구") & (master["단지명"] == "사가정센트럴아이파크")
    ].copy()
    sub["계약일자"] = pd.to_datetime(sub["계약일자"])
    sub = sub.sort_values("계약일자")

    if sub.empty:
        print("  -> 경고: 사가정센트럴아이파크 거래 데이터가 없어 차트2를 건너뜁니다.")
        return

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(sub["계약일자"], sub["평단가"], color="#999999", linewidth=1, zorder=1)

    for policy, color in [(PRE, COLOR_PRE), (POST, COLOR_POST)]:
        part = sub[sub["정책여부"] == policy]
        ax.scatter(
            part["계약일자"], part["평단가"], color=color, s=28,
            label=policy, zorder=2, edgecolors="white", linewidths=0.4,
        )

    ax.axvline(POLICY_DATE, color="black", linestyle="--", linewidth=1.2)
    ax.text(
        POLICY_DATE, ax.get_ylim()[1], " 정책 시행일(2025-06-28)",
        rotation=90, va="top", ha="left", fontsize=9,
    )

    ax.set_xlabel("계약일자")
    ax.set_ylabel("평단가 (만원/평)")
    ax.set_title("중랑구 사가정센트럴아이파크 평단가 시계열")
    ax.legend()
    fig.tight_layout()
    _savefig(fig, "2_사가정센트럴아이파크_시계열.png")

    pre_out = sub.loc[sub["정책여부"] == PRE, "이상치여부"].mean() * 100
    post_out = sub.loc[sub["정책여부"] == POST, "이상치여부"].mean() * 100
    print(
        f"  -> 거래 {len(sub)}건, 이상치 비율 정책전 {pre_out:.1f}% -> "
        f"정책후 {post_out:.1f}%"
    )


# ---------------------------------------------------------------------------
# 3. 월별 거래량 추이 (전체 합산 + 상위 5개 구)
# ---------------------------------------------------------------------------

def chart3_monthly_volume(master: pd.DataFrame) -> None:
    tmp = master.copy()
    tmp["계약일자"] = pd.to_datetime(tmp["계약일자"])
    tmp["계약년월"] = tmp["계약일자"].dt.to_period("M").dt.to_timestamp()

    # 마지막 달은 데이터 수집 시점(2026-08-15)에 잘려 있어 거래량이 실제보다
    # 적게 집계되므로(정책 효과가 아닌 수집 컷오프 아티팩트) 제외한다.
    last_month = tmp["계약년월"].max()
    tmp = tmp[tmp["계약년월"] < last_month]

    total = tmp.groupby("계약년월").size().sort_index()
    top5_gu = tmp["구"].value_counts().head(5).index.tolist()
    by_gu = (
        tmp[tmp["구"].isin(top5_gu)]
        .groupby(["계약년월", "구"]).size()
        .unstack("구")
        .reindex(total.index)
    )

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(total.index, total.values, color="black", linewidth=2.4, label="서울 전체(25개 구 합산)")
    for gu in top5_gu:
        ax.plot(by_gu.index, by_gu[gu], linewidth=1.4, marker="o", markersize=3, label=gu)

    ax.axvline(POLICY_DATE, color="red", linestyle="--", linewidth=1.2)
    ax.text(POLICY_DATE, ax.get_ylim()[1], " 정책 시행일", rotation=90, va="top", ha="left", fontsize=9, color="red")

    ax.set_xlabel("계약년월")
    ax.set_ylabel("거래건수")
    ax.set_title("월별 거래량 추이: 서울 전체 vs 거래량 상위 5개 구")
    ax.legend(ncol=2, fontsize=9)
    fig.tight_layout()
    _savefig(fig, "3_월별거래량_추이.png")

    print(f"  -> 거래량 상위 5개 구: {top5_gu}")


# ---------------------------------------------------------------------------
# 4. 신축 비중 vs 데이터 이슈 건수 산점도
# ---------------------------------------------------------------------------

def chart4_newbuild_vs_issues(master: pd.DataFrame) -> None:
    BUSINESS_KEY = ["구", "법정동", "단지명", "계약일자", "층", "거래금액"]
    NEAR_DUP_KEY = ["구", "법정동", "단지명", "계약일자", "거래금액"]

    newbuild_share = (
        master.assign(신축=lambda d: d["연식"] <= 5)
        .groupby("구")["신축"].mean() * 100
    )

    conflicts = pd.read_csv(os.path.join(PROCESSED_DIR, "business_key_conflicts.csv"))
    near_dup = pd.read_csv(os.path.join(PROCESSED_DIR, "near_duplicate_candidates.csv"))

    conflict_groups = (
        conflicts.drop_duplicates(subset=BUSINESS_KEY)["구"].value_counts()
    )
    near_dup_groups = (
        near_dup.drop_duplicates(subset=NEAR_DUP_KEY)["구"].value_counts()
    )

    gu_list = master["구"].unique()
    issue_counts = (
        conflict_groups.reindex(gu_list, fill_value=0)
        + near_dup_groups.reindex(gu_list, fill_value=0)
    )

    plot_df = pd.DataFrame({
        "신축비중": newbuild_share.reindex(gu_list),
        "이슈그룹수": issue_counts,
    }).reset_index(names="구")

    plot_df = plot_df.sort_values("신축비중").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.scatter(plot_df["신축비중"], plot_df["이슈그룹수"], s=60, color="#4C72B0", alpha=0.8)
    for i, row in plot_df.iterrows():
        # 인접한 점들의 라벨이 겹치지 않도록 위/아래로 번갈아 배치한다.
        dy = 6 if i % 2 == 0 else -12
        ax.annotate(
            row["구"], (row["신축비중"], row["이슈그룹수"]),
            xytext=(5, dy), textcoords="offset points", fontsize=8,
        )

    ax.set_xlabel("연식 5년 이하 거래 비중 (%)")
    ax.set_ylabel("데이터 이슈 그룹 수 (재수집충돌 + 근접중복)")
    ax.set_title("구별 신축 비중 vs 데이터 이슈 건수")
    ax.margins(x=0.12, y=0.1)
    fig.tight_layout()
    _savefig(fig, "4_신축비중_vs_데이터이슈_산점도.png")

    corr = plot_df["신축비중"].corr(plot_df["이슈그룹수"])
    print(f"  -> 신축비중-이슈그룹수 상관계수: {corr:.2f}")


# ---------------------------------------------------------------------------
# 5. 구별 변동률(%) 지도
# ---------------------------------------------------------------------------

def chart5_gu_change_map(master: pd.DataFrame) -> None:
    agg = pd.read_csv(os.path.join(PROCESSED_DIR, "gu_dong_month_avg_price.csv"))

    # 2025-06은 정책 시행일(6/28)이 포함된 전환월이라 정책전/후가 섞여 있으므로
    # 완전한 월만 사용하고 이 달은 계산에서 제외한다.
    agg = agg[agg["계약년월"] != "2025-06"].copy()
    agg["period"] = np.where(agg["계약년월"] < "2025-06", PRE, POST)

    gu_period = (
        agg.assign(가중합=agg["평균평단가"] * agg["거래건수"])
        .groupby(["구", "period"])
        .agg(가중합=("가중합", "sum"), 거래건수=("거래건수", "sum"))
        .reset_index()
    )
    gu_period["가중평균평단가"] = gu_period["가중합"] / gu_period["거래건수"]

    pivot = gu_period.pivot(index="구", columns="period", values="가중평균평단가")
    pivot["변동률"] = (pivot[POST] - pivot[PRE]) / pivot[PRE] * 100

    with open(os.path.join(OUT_DIR, "seoul_gu_boundaries.geojson"), encoding="utf-8") as f:
        geo = json.load(f)

    vmax = pivot["변동률"].abs().max()
    cmap = plt.get_cmap("RdBu_r")
    norm = plt.Normalize(vmin=-vmax, vmax=vmax)

    fig, ax = plt.subplots(figsize=(9, 9))
    for feature in geo["features"]:
        gu_name = feature["properties"]["SIG_KOR_NM"]
        change = pivot.loc[gu_name, "변동률"] if gu_name in pivot.index else np.nan
        color = cmap(norm(change)) if pd.notna(change) else "#DDDDDD"

        geom = feature["geometry"]
        if geom["type"] == "Polygon":
            rings = [geom["coordinates"][0]]
        else:
            rings = [poly[0] for poly in geom["coordinates"]]

        for ring in rings:
            xy = np.array(ring)
            ax.add_patch(Polygon(xy, closed=True, facecolor=color, edgecolor="white", linewidth=0.8))

        cx, cy = np.mean(rings[0], axis=0)
        ax.annotate(gu_name, (cx, cy), fontsize=6.5, ha="center", va="center")

    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("구별 정책전 -> 정책후 평단가 변동률 (%)")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("변동률 (%)")

    fig.tight_layout()
    _savefig(fig, "5_구별_변동률_지도.png")

    top = pivot["변동률"].sort_values(ascending=False)
    print(f"  -> 변동률 최고: {top.index[0]} ({top.iloc[0]:+.1f}%), "
          f"최저: {top.index[-1]} ({top.iloc[-1]:+.1f}%)")


# ---------------------------------------------------------------------------
# 6. 계약취소(해제신고) 비율의 월별 추이 (원본 raw 파일 기준)
# ---------------------------------------------------------------------------

def chart6_cancellation_rate() -> None:
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    frames = []
    for fp in files:
        df = pd.read_csv(
            fp, encoding="utf-8-sig", dtype=str,
            usecols=["계약년월", "해제사유발생일"],
        )
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)

    raw["취소여부"] = raw["해제사유발생일"].fillna("").astype(str).str.strip() != ""
    monthly = raw.groupby("계약년월").agg(전체=("취소여부", "size"), 취소=("취소여부", "sum"))
    monthly["취소율"] = monthly["취소"] / monthly["전체"] * 100
    monthly.index = pd.to_datetime(monthly.index, format="%Y%m")
    monthly = monthly.sort_index()

    # 마지막 달은 수집 시점(2026-08-15)에 잘려 표본이 작아 취소율이 튈 수
    # 있으므로 제외한다 (계약 후 해제신고까지 시차가 있어 최근월은 특히 과소집계됨).
    monthly = monthly.iloc[:-1]

    # 해제신고는 계약일 대비 중앙값 28일, 90분위 약 95일의 시차를 두고
    # 발생한다. 데이터 수집 시점(2026-08-15) 직전 몇 개월은 아직 해제신고가
    # 누적될 시간이 부족해 취소율이 실제보다 낮게 집계되는 "우측 절단"이
    # 생기므로, 이 구간을 시각적으로 표시해 오독을 방지한다.
    censored_start = monthly.index.max() - pd.DateOffset(months=3)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(monthly.index, monthly["취소율"], color="#C44E52", marker="o", markersize=4, linewidth=1.6)
    ax.axvline(POLICY_DATE, color="black", linestyle="--", linewidth=1.2)
    ax.text(POLICY_DATE, ax.get_ylim()[1], " 정책 시행일(2025-06-28)", rotation=90, va="top", ha="left", fontsize=9)

    ax.axvspan(censored_start, monthly.index.max() + pd.DateOffset(days=15), color="grey", alpha=0.15)
    ax.text(
        censored_start, ax.get_ylim()[1], " 집계 지연 구간(우측절단, 취소율 과소추정 가능) ",
        rotation=90, va="top", ha="left", fontsize=8, color="dimgray",
    )

    ax.set_xlabel("계약년월")
    ax.set_ylabel("계약취소(해제신고) 비율 (%)")
    ax.set_title("월별 계약취소 비율 추이 (원본 raw 데이터 기준)")
    fig.tight_layout()
    _savefig(fig, "6_계약취소비율_월별추이.png")

    stable = monthly[monthly.index < censored_start]
    pre_avg = stable.loc[stable.index < "2025-06", "취소율"].mean()
    post_avg = stable.loc[stable.index > "2025-06", "취소율"].mean()
    print(
        f"  -> (우측절단 제외 안정 구간 기준) 정책전 평균 취소율 {pre_avg:.2f}% -> "
        f"정책후 평균 취소율 {post_avg:.2f}%"
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    master = pd.read_csv(os.path.join(PROCESSED_DIR, "apt_master.csv"))

    print("[1/6] 평단가 분포 히스토그램")
    chart1_price_distribution(master)

    print("[2/6] 사가정센트럴아이파크 시계열")
    chart2_sagajeong_timeseries(master)

    print("[3/6] 월별 거래량 추이")
    chart3_monthly_volume(master)

    print("[4/6] 신축비중 vs 데이터이슈 산점도")
    chart4_newbuild_vs_issues(master)

    print("[5/6] 구별 변동률 지도")
    chart5_gu_change_map(master)

    print("[6/6] 계약취소 비율 월별 추이")
    chart6_cancellation_rate()


if __name__ == "__main__":
    main()
