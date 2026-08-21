"""data/ CSV 로더. 캐싱과 이상치·미집계월 필터 기본값을 여기서 한 번만 처리한다.

실제 파이프라인 산출물이 올라오기 전까지는 data/*.csv가 플레이스홀더 데이터다.
컬럼 이름과 계산 규칙은 README.md '데이터 계약' / '계산 규칙' 절을 따른다.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

POLICY_SPLIT_DATE = pd.Timestamp("2025-06-28")  # 이 날짜부터 '정책 후'
UNSETTLED_MONTH = "2026-08"  # 신고 기간이 남아있어 집계에서 제외하는 달


def _read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"{name} 이 data/ 폴더에 없습니다. 실제 파이프라인 산출물을 data/에 복사해 주세요."
        )
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def load_apt_master(exclude_outlier: bool = True, exclude_unsettled_month: bool = True) -> pd.DataFrame:
    df = _read_csv("apt_master.csv")
    df["계약일자"] = pd.to_datetime(df["계약일자"])
    df["계약연월"] = df["계약일자"].dt.strftime("%Y-%m")
    df["정책여부"] = df["정책여부"].fillna(
        df["계약일자"].apply(lambda d: "정책후" if d >= POLICY_SPLIT_DATE else "정책전")
    )
    if exclude_outlier and "이상치여부" in df.columns:
        df = df[~df["이상치여부"].astype(bool)]
    if exclude_unsettled_month:
        df = df[df["계약연월"] != UNSETTLED_MONTH]
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_gu_dong_month_avg_price() -> pd.DataFrame:
    df = _read_csv("gu_dong_month_avg_price.csv")
    return df[df["계약년월"] != UNSETTLED_MONTH].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_news(source: str = "category") -> pd.DataFrame:
    """source: 'keyword' -> news_titles.csv, 'category' -> news_titles_category.csv"""
    name = "news_titles.csv" if source == "keyword" else "news_titles_category.csv"
    df = _read_csv(name)
    df["날짜"] = pd.to_datetime(df["날짜"])
    return df


@st.cache_data(show_spinner=False)
def load_sentiment_summary() -> pd.DataFrame:
    return _read_csv("sentiment_summary.csv")


def data_files_missing() -> list[str]:
    required = [
        "apt_master.csv",
        "gu_dong_month_avg_price.csv",
        "news_titles.csv",
        "news_titles_category.csv",
        "sentiment_summary.csv",
    ]
    return [name for name in required if not (DATA_DIR / name).exists()]


def guard_or_stop():
    """data/ 파일이 없으면 안내 메시지를 띄우고 스크립트를 멈춘다. 페이지마다 반복되던 체크를 한곳에 모았다."""
    missing = data_files_missing()
    if missing:
        st.error(
            "data/ 폴더에 다음 파일이 없어 화면을 채울 수 없습니다: "
            + ", ".join(missing)
            + "\n\n실제 파이프라인 산출물이 올라오기 전까지는 임시(mock) 데이터로 확인해 주세요."
        )
        st.stop()
