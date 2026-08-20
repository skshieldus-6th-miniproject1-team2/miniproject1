"""
서울 아파트 실거래가(국토교통부) 전처리 파이프라인

seoul_raw_data/ 폴더에 있는
    {구}_{정책전|정책후}_{시작일}_{종료일}.csv
형태의 파일들을 모두 읽어 하나의 스키마로 합치고, 정제/파생변수 생성 후
processed/apt_master.csv 로 저장한다.
목적: 정책 시행 전후 지역별 평단가 변동률 분석 + 향후 ML 예측용 데이터 준비.

사용법:
    python pipeline.py
    python pipeline.py --raw-dir seoul_raw_data --out-dir processed
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

FILENAME_RE = re.compile(
    r"^(?P<gu>[가-힣]+)_(?P<policy>정책전|정책후)_(?P<start>\d{8})_(?P<end>\d{8})\.csv$"
)

RAW_COLUMNS = [
    "NO", "시군구", "번지", "본번", "부번", "단지명", "전용면적(㎡)", "계약년월", "계약일",
    "거래금액(만원)", "동", "층", "매수자", "매도자", "건축년도", "도로명",
    "해제사유발생일", "거래유형", "중개사소재지", "등기일자",
]

FINAL_COLUMNS = [
    "구", "법정동", "단지명", "계약일자", "전용면적", "평형", "거래금액",
    "평단가", "층", "건축년도", "연식", "거래유형", "정책여부", "이상치여부",
]

# 재수집(같은 구간이 다른 종료일로 다시 다운로드되는 경우) 시 동일 실거래를
# 식별하는 키. 이 키가 겹치면 같은 거래로 간주하고 가장 최근에 내려받은
# 파일의 값으로 유지한다.
BUSINESS_KEY = ["구", "법정동", "단지명", "계약일자", "층", "거래금액"]

# "완전 중복은 아니지만 의심되는" 사례 탐지 키. 같은 단지/같은 날/같은 금액인데
# 층이 다르면(=BUSINESS_KEY로는 안 걸림) 데이터 입력 실수 가능성이 있어
# 별도로 리포트만 하고 자동으로 지우지는 않는다.
NEAR_DUP_KEY = ["구", "법정동", "단지명", "계약일자", "거래금액"]

# BUSINESS_KEY가 겹치는 행들 사이에서, 이 컬럼들의 non-null 값이 서로
# 일치하는지로 "같은 거래의 중복 신고(안전 병합)"와 "우연히 겹친 서로 다른
# 거래(병합 보류)"를 구분한다. (검증 결과: 동/등기일자 등은 채워지는 시점이
# 파일 내 행 순서와 무관해서, 단순히 "값이 있으면 최신"이라고 가정할 수 없었음)
BUSINESS_KEY_CONFLICT_COLS = [
    "동", "매수자", "매도자", "도로명", "거래유형", "등기일자", "전용면적(㎡)",
]

PYEONG_DIVISOR = 3.3058  # 1평 = 3.3058 m^2
AREA_BIN_WIDTH = 20      # 이상치 탐지용 전용면적 구간 폭(㎡)
MIN_GROUP_SIZE = 5       # 이 값보다 작은 그룹은 IQR이 불안정하므로 이상치 판정 보류


# ---------------------------------------------------------------------------
# 1. 원본 로드
# ---------------------------------------------------------------------------

def parse_filename(path: str) -> tuple[str, str, str]:
    """파일명에서 (구, 정책여부, 종료일)을 파싱한다."""
    base = os.path.basename(path)
    m = FILENAME_RE.match(base)
    if not m:
        raise ValueError(
            f"파일명이 규칙({{구}}_{{정책전|정책후}}_{{시작일}}_{{종료일}}.csv)과 맞지 않습니다: {base}"
        )
    return m.group("gu"), m.group("policy"), m.group("end")


def load_raw(raw_dir: str) -> pd.DataFrame:
    """raw_dir 안의 모든 csv를 읽어 하나의 DataFrame으로 합친다.

    같은 구간을 다시 받은 파일이 섞여 있을 수 있으므로, 파일 수정시각과
    파일명의 종료일을 기준으로 '오래된 파일 -> 최신 파일' 순으로 정렬해
    이후 재수집 dedup(keep='last')에서 최신 파일이 우선하도록 한다.
    """
    files = sorted(glob.glob(os.path.join(raw_dir, "*.csv")))
    if not files:
        raise FileNotFoundError(f"'{raw_dir}'에서 csv 파일을 찾지 못했습니다.")

    frames = []
    for fp in files:
        gu_from_name, policy, end_date = parse_filename(fp)
        df = pd.read_csv(fp, encoding="utf-8-sig", dtype=str)

        missing = set(RAW_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"{os.path.basename(fp)}: 예상 컬럼 누락 -> {missing}")

        df["_원본파일_구"] = gu_from_name
        df["정책여부"] = policy
        df["_파일종료일"] = end_date
        df["_파일수정시각"] = os.path.getmtime(fp)
        frames.append(df)

    raw = pd.concat(frames, ignore_index=True)
    raw = raw.sort_values(
        ["_파일수정시각", "_파일종료일"], kind="stable"
    ).reset_index(drop=True)

    print(f"[load_raw] 파일 {len(files)}개, 총 {len(raw):,}행 로드 완료")
    return raw


# ---------------------------------------------------------------------------
# 2. 이상치 플래그 (전용면적 구간별 그룹 IQR, 평단가 기준)
# ---------------------------------------------------------------------------

def _iqr_outlier_mask(values: pd.Series, min_group_size: int = MIN_GROUP_SIZE) -> pd.Series:
    if len(values) < min_group_size:
        return pd.Series(False, index=values.index)
    q1, q3 = values.quantile(0.25), values.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return pd.Series(False, index=values.index)
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return (values < lower) | (values > upper)


def resolve_business_key_duplicates(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """BUSINESS_KEY가 겹치는 행들을 안전 병합 대상과 충돌(병합 보류) 대상으로 나눈다.

    - 그룹 내 BUSINESS_KEY_CONFLICT_COLS 각각의 non-null 값이 전부 일치하면
      (=한쪽이 다른쪽의 부분집합, 예: 등기 전/후로 같은 거래가 중복 신고된 경우)
      가장 정보가 많이 채워진 행 하나만 남긴다.
    - 하나라도 서로 다른 non-null 값이 있으면(예: 동/등기일자가 서로 다름)
      실제로는 다른 세대의 거래일 가능성이 높으므로 병합하지 않고 두 행 모두
      보존한 채 별도로 리포트한다.

    반환: (병합/보존 완료된 df, 안전 병합으로 제거된 행, 충돌로 보류된 행)
    """
    key_cols = BUSINESS_KEY
    grp_size = df.groupby(key_cols)["NO"].transform("size")
    unique_part = df[grp_size == 1]
    dup_part = df[grp_size > 1]

    if dup_part.empty:
        return df, df.iloc[0:0], df.iloc[0:0]

    safe_kept, safe_removed, conflicts = [], [], []
    for _, g in dup_part.groupby(key_cols, sort=False):
        conflict = any(
            g[col].dropna().nunique() > 1 for col in BUSINESS_KEY_CONFLICT_COLS
        )
        if conflict:
            conflicts.append(g)
        else:
            completeness = g[BUSINESS_KEY_CONFLICT_COLS].notna().sum(axis=1)
            best_idx = completeness.idxmax()
            safe_kept.append(g.loc[[best_idx]])
            safe_removed.append(g.drop(index=best_idx))

    safe_kept_df = pd.concat(safe_kept) if safe_kept else dup_part.iloc[0:0]
    safe_removed_df = pd.concat(safe_removed) if safe_removed else dup_part.iloc[0:0]
    conflicts_df = pd.concat(conflicts) if conflicts else dup_part.iloc[0:0]

    result = pd.concat([unique_part, safe_kept_df, conflicts_df]).sort_index()
    return result, safe_removed_df, conflicts_df


def flag_outliers(df: pd.DataFrame) -> pd.Series:
    """구 x 전용면적구간 그룹별로 평단가에 대한 IQR 이상치를 판정한다.

    전체를 한 그룹으로 묶지 않는 이유:
    - 지역별 평단가 수준이 크게 달라 강남 3구 등 고가 지역 거래가
      통째로 '이상치'가 되어버리는 왜곡을 방지하기 위함 (구 단위 분리)
    - 소형 평형은 원래 평단가가 높게 나오는 경향이 있어, 이를 무시하고
      전체 IQR을 적용하면 정상적인 소형 평형 거래가 이상치로 잘못
      걸릴 수 있음 (전용면적 구간 분리)
    펜트하우스/특수관계자 거래 등 의미 있는 케이스일 수 있으므로
    삭제하지 않고 플래그만 남긴다.
    """
    max_area = df["전용면적"].max()
    bins = np.arange(0, max_area + AREA_BIN_WIDTH, AREA_BIN_WIDTH)
    area_bin = pd.cut(df["전용면적"], bins=bins, right=False)

    mask = (
        df.groupby([df["구"], area_bin], observed=True)["평단가"]
        .transform(_iqr_outlier_mask)
    )
    return mask.astype(bool)


# ---------------------------------------------------------------------------
# 3. 정제 + 파생변수
# ---------------------------------------------------------------------------

def clean(
    raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """정제를 수행하고 (최종 데이터, 의심 중복 리포트, 재수집 제거 감사로그,
    비즈니스키 충돌 리포트, 단계별 건수 요약)을 반환한다."""
    df = raw.copy()
    stats = {"원본": len(df)}

    # (1) 계약 취소건 제외 (해제사유발생일이 not null / 공백 아님)
    #     -> 파기된 거래는 실제 시장가를 반영하지 않아 정책효과 분석에 노이즈가 됨
    cancel_mask = df["해제사유발생일"].fillna("").astype(str).str.strip() != ""
    n_cancel = int(cancel_mask.sum())
    df = df[~cancel_mask].copy()
    stats["계약취소_제외"] = n_cancel
    stats["취소건_제외후"] = len(df)

    # (2) 완전 중복행 제거 (NO는 파일 내부 일련번호일 뿐이라 비교에서 제외)
    dedup_cols = [c for c in df.columns if c != "NO"]
    before = len(df)
    df = df.drop_duplicates(subset=dedup_cols, keep="last")
    stats["완전중복_제거"] = before - len(df)
    stats["완전중복_제거후"] = len(df)

    # (3) 거래금액(만원) 콤마 제거 -> 정수 변환
    df["거래금액"] = (
        df["거래금액(만원)"].astype(str).str.replace(",", "", regex=False).astype(int)
    )

    # (4) 계약년월 + 계약일 -> 계약일자(datetime)
    df["계약일자"] = pd.to_datetime(
        df["계약년월"].astype(str) + df["계약일"].astype(str).str.zfill(2),
        format="%Y%m%d",
    )

    # (5) 시군구 -> 구 / 법정동 분리 (파일명이 아닌 실제 시군구 값을 신뢰)
    #     예: "서울특별시 강남구 개포동" -> 구="강남구", 법정동="개포동"
    sigungu_parts = df["시군구"].str.split(" ", n=2, expand=True)
    df["구"] = sigungu_parts[1]
    df["법정동"] = sigungu_parts[2]

    mismatch = df["구"] != df["_원본파일_구"]
    if mismatch.any():
        print(
            f"[clean] 참고: 파일명 상 구와 실제 시군구 상 구가 다른 행 {mismatch.sum()}건 "
            f"발견 (시군구 값을 기준으로 처리함)"
        )

    # (6) 전용면적 / 평형 / 평단가 / 연식
    df["전용면적"] = df["전용면적(㎡)"].astype(float)
    df["평형"] = df["전용면적"] / PYEONG_DIVISOR
    df["평단가"] = df["거래금액"] / df["평형"]
    df["건축년도"] = df["건축년도"].astype(int)
    df["연식"] = df["계약일자"].dt.year - df["건축년도"]
    df["층"] = df["층"].astype(int)

    # (7) 재수집 dedup: 동일 실거래(구/법정동/단지명/계약일자/층/거래금액)가
    #     서로 다른 다운로드본(또는 같은 파일 내 '등기 전/후' 두 스냅샷)에
    #     겹쳐 들어온 경우를 정리한다.
    #     -> 동/매수자/매도자/도로명/거래유형/등기일자/전용면적 중 서로 다른
    #        non-null 값이 하나라도 있으면 실제로는 다른 세대의 거래일 수
    #        있으므로 병합하지 않고 둘 다 보존한 채 별도 리포트만 한다.
    #        (검증 결과 "행 순서가 나중 = 더 완전한 정보"라는 가정이 성립하지
    #        않아, 정보량이 가장 많은 행을 남기는 방식으로 바꿈)
    before_bk = len(df)
    df, removed_bk, conflicts_bk = resolve_business_key_duplicates(df)
    stats["재수집_중복_제거"] = len(removed_bk)
    stats["재수집_중복_제거후"] = len(df)
    stats["재수집_충돌_보류_행수"] = len(conflicts_bk)
    stats["재수집_충돌_보류_그룹수"] = (
        conflicts_bk.groupby(BUSINESS_KEY, dropna=False).ngroups if len(conflicts_bk) else 0
    )
    assert before_bk == len(df) + len(removed_bk)

    # (8) 이상치여부 플래그 (삭제하지 않음)
    df["이상치여부"] = flag_outliers(df)
    stats["이상치_플래그"] = int(df["이상치여부"].sum())

    # (9) 의심 중복 리포트: 완전/재수집 중복은 아니지만 같은 단지/같은 날/
    #     같은 금액인데 층만 다른 경우 -> 자동 제거하지 않고 별도로 알려줌
    dup_flag = df.duplicated(subset=NEAR_DUP_KEY, keep=False)
    near_dup = (
        df.loc[dup_flag, ["구", "법정동", "단지명", "계약일자", "층", "전용면적", "거래금액", "정책여부"]]
        .sort_values(["구", "법정동", "단지명", "계약일자", "층"])
        .reset_index(drop=True)
    )
    stats["의심중복_행수"] = len(near_dup)
    stats["의심중복_그룹수"] = (
        near_dup.groupby(NEAR_DUP_KEY, dropna=False).ngroups if len(near_dup) else 0
    )

    audit_cols = [
        "구", "법정동", "단지명", "전용면적(㎡)", "계약일자", "층", "거래금액",
        "동", "매수자", "매도자", "도로명", "거래유형", "등기일자", "정책여부",
    ]
    removed_bk = removed_bk[audit_cols].sort_values(
        ["구", "법정동", "단지명", "계약일자", "층"]
    ).reset_index(drop=True)
    conflicts_bk = conflicts_bk[audit_cols].sort_values(
        ["구", "법정동", "단지명", "계약일자", "층"]
    ).reset_index(drop=True)

    result = (
        df[FINAL_COLUMNS]
        .sort_values(["구", "법정동", "계약일자"])
        .reset_index(drop=True)
    )
    stats["최종"] = len(result)

    return result, near_dup, removed_bk, conflicts_bk, stats


def print_summary(stats: dict) -> None:
    print("\n===== 단계별 처리 건수 요약 =====")
    print(f"  원본 로드                : {stats['원본']:>8,} 행")
    print(f"  - 계약취소 제외          : {stats['계약취소_제외']:>8,} 행 제외 -> {stats['취소건_제외후']:>8,} 행")
    print(f"  - 완전 중복 제거         : {stats['완전중복_제거']:>8,} 행 제거 -> {stats['완전중복_제거후']:>8,} 행")
    print(f"  - 재수집 중복 제거(안전) : {stats['재수집_중복_제거']:>8,} 행 제거 -> {stats['재수집_중복_제거후']:>8,} 행")
    print(f"  - 재수집 충돌(병합보류)  : {stats['재수집_충돌_보류_행수']:>8,} 행 보존 ({stats['재수집_충돌_보류_그룹수']:,} 그룹, 삭제하지 않음)")
    print(f"  - 이상치 플래그(비삭제)  : {stats['이상치_플래그']:>8,} 행 플래그")
    print(f"  - 의심 중복(리포트만)    : {stats['의심중복_행수']:>8,} 행 ({stats['의심중복_그룹수']:,} 그룹)")
    print(f"  최종 저장 행수           : {stats['최종']:>8,} 행")
    print("=================================\n")


# ---------------------------------------------------------------------------
# 4. 구 x 동 x 월 평균 평단가 집계
# ---------------------------------------------------------------------------

def aggregate_monthly_price(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df.copy()
    tmp["계약년월"] = tmp["계약일자"].dt.to_period("M").astype(str)

    agg = (
        tmp.groupby(["구", "법정동", "계약년월"], as_index=False)
        .agg(
            평균평단가=("평단가", "mean"),
            중위평단가=("평단가", "median"),
            거래건수=("평단가", "size"),
        )
        .sort_values(["구", "법정동", "계약년월"])
        .reset_index(drop=True)
    )
    agg["평균평단가"] = agg["평균평단가"].round(1)
    agg["중위평단가"] = agg["중위평단가"].round(1)
    return agg


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def run(raw_dir: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)

    raw = load_raw(raw_dir)
    clean_df, near_dup_df, removed_bk_df, conflicts_bk_df, stats = clean(raw)
    print_summary(stats)

    master_path = os.path.join(out_dir, "apt_master.csv")
    clean_df.to_csv(master_path, index=False, encoding="utf-8-sig")
    print(f"[run] 정제 마스터 저장 -> {master_path} ({len(clean_df):,}행)")

    if len(removed_bk_df):
        removed_bk_path = os.path.join(out_dir, "business_key_dedup_removed.csv")
        removed_bk_df.to_csv(removed_bk_path, index=False, encoding="utf-8-sig")
        print(
            f"[run] 재수집(비즈니스키) 안전 병합 감사 로그 -> {removed_bk_path} "
            f"({len(removed_bk_df):,}행) - 병합되어 사라진 행 (모든 필드가 일치/보완 관계였음)"
        )

    if len(conflicts_bk_df):
        conflicts_bk_path = os.path.join(out_dir, "business_key_conflicts.csv")
        conflicts_bk_df.to_csv(conflicts_bk_path, index=False, encoding="utf-8-sig")
        print(
            f"[run] 재수집(비즈니스키) 충돌 리포트 -> {conflicts_bk_path} "
            f"({len(conflicts_bk_df):,}행) - 동/등기일자 등이 서로 달라 병합하지 않고 "
            f"master에 그대로 남겨둔 행. 실제로 다른 세대의 거래일 가능성이 높으니 직접 확인 필요"
        )

    if len(near_dup_df):
        near_dup_path = os.path.join(out_dir, "near_duplicate_candidates.csv")
        near_dup_df.to_csv(near_dup_path, index=False, encoding="utf-8-sig")
        print(
            f"[run] 의심 중복 리포트 저장 -> {near_dup_path} "
            f"({len(near_dup_df):,}행, {stats['의심중복_그룹수']:,}그룹) "
            f"- 자동 삭제하지 않았으니 직접 확인 필요"
        )
    else:
        print("[run] 의심 중복 사례 없음")

    agg_df = aggregate_monthly_price(clean_df)
    agg_path = os.path.join(out_dir, "gu_dong_month_avg_price.csv")
    agg_df.to_csv(agg_path, index=False, encoding="utf-8-sig")
    print(f"[run] 구x동x월 집계 저장 -> {agg_path} ({len(agg_df):,}행)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", default="seoul_raw_data", help="원본 csv 폴더")
    parser.add_argument("--out-dir", default="processed", help="결과 저장 폴더")
    args = parser.parse_args()

    try:
        run(args.raw_dir, args.out_dir)
    except (FileNotFoundError, ValueError) as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
