"""data/ CSV 로더. 캐싱과 데이터 없음 안내를 여기서 한 번만 처리한다.

부동산(아파트) 데이터는 apt_master.csv(161,512행)가 도착해 화면이 정상 작동한다.
gu_dong_month_avg_price.csv(구·동·월 집계본)는 아직 없지만, 현재 어떤 화면도 이 파일을
직접 읽지 않는다 — 월별/구별 집계는 apt_master.csv에서 lib/metrics.py가 그때그때 계산한다.
그래서 `guard_apt_or_stop()`의 필수 파일 목록에는 넣지 않는다 (안 쓰는 파일 때문에 화면을
막으면 안 된다). 나중에 실제로 그 파일을 쓰는 코드가 생기면 APT_FILES에 다시 추가할 것.

뉴스 데이터는 webscraping 브랜치 산출물로 교체됐다. 실제 파일 5개:
- News_Scraping.csv          : 기사 단위, 감정 3그룹(긍정/부정/중립) — 참고용, 다른 파일로 대체됨
- News_Scraping_retouch.csv  : 기사 단위, 감정 7종 + 확률(수치) — 세부 감정·기사 탐색에 사용
- News_Scraping_summary.csv  : 정책 구분 없이 전체 전/후 감정 비율 1건
- j_News_Scraping.csv        : 기사 단위, '시기'가 "정책_단계"(예: "6·27_시행전") 또는 "평시".
                                기업/소비자/시장 3개 관점별 감정을 따로 담고 있다.
- j_News_Scraping_summary.csv: 정책 × 관점 × 전/후 감정 비율 집계 (긍정/중립/부정 합 100)

News_Scraping_retouch.csv의 '정책' 컬럼은 전체 행이 "6·27 가계부채 관리 강화방안"으로
고정돼 있어(파이프라인 미완성 추정) 정책 구분에 못 쓴다. 그래서 기사 단위로 정책·단계가
필요한 곳은 j_News_Scraping.csv의 '시기'를 파싱해서 쓰고, url 기준으로 두 파일을 합쳐
(감정 7종 + 확률) + (정책 + 단계)를 한 표로 만든다 (`load_news_articles`).
"""
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

APT_FILES = ["apt_master.csv"]
NEWS_FILES = [
    "News_Scraping_retouch.csv",
    "j_News_Scraping.csv",
    "j_News_Scraping_summary.csv",
    "News_Scraping_summary.csv",
]

POLICY_SPLIT_DATE = pd.Timestamp("2025-06-28")  # 이 날짜부터 '정책 후'
UNSETTLED_MONTH = "2026-08"  # 신고 기간이 남아있어 집계에서 제외하는 달


def _read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"{name} 이 data/ 폴더에 없습니다. 실제 파이프라인 산출물을 data/에 복사해 주세요."
        )
    return pd.read_csv(path, encoding="utf-8-sig")


# ---------------------------------------------------------------- 부동산 (아직 미도착)
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


# ---------------------------------------------------------------- 뉴스 (실 데이터)
@st.cache_data(show_spinner=False)
def load_news_detail() -> pd.DataFrame:
    """News_Scraping_retouch.csv — 기사 단위 7종 감정 + 확률. '정책'/'대통령' 컬럼은 전체가 같은 값이라 쓰지 않는다."""
    df = _read_csv("News_Scraping_retouch.csv")
    df["날짜"] = pd.to_datetime(df["날짜"])
    return df


@st.cache_data(show_spinner=False)
def load_news_perspective() -> pd.DataFrame:
    """j_News_Scraping.csv — '시기'를 정책/단계로 분리해서 반환한다 ("6·27_시행전" → 정책 6·27, 단계 시행전)."""
    df = _read_csv("j_News_Scraping.csv")
    df["날짜"] = pd.to_datetime(df["날짜"])
    split = df["시기"].str.split("_", n=1, expand=True)
    is_normal = df["시기"] == "평시"
    df["정책"] = split[0].where(~is_normal, "평시")
    df["단계"] = split[1].where(~is_normal, "평시")
    return df


@st.cache_data(show_spinner=False)
def load_news_articles() -> pd.DataFrame:
    """기사 단위 통합표 — url 기준으로 (감정 7종·확률)과 (정책·단계)를 합친다.

    감정별 기사 탐색, 시점별 감정 분포처럼 정책 단위 필터링이 필요한 화면은 전부 이 표를 쓴다.
    """
    detail = load_news_detail()[["날짜", "기사제목", "url", "감정", "수치"]]
    perspective = load_news_perspective()[["url", "정책", "단계", "기업_감정", "소비자_감정", "시장_감정"]]
    return detail.merge(perspective, on="url", how="inner")


@st.cache_data(show_spinner=False)
def load_news_perspective_summary() -> pd.DataFrame:
    """j_News_Scraping_summary.csv — 정책 × 관점 × 전/후 감정 비율(0~100%). 100으로 나눠 비율(0~1)로 맞춘다."""
    df = _read_csv("j_News_Scraping_summary.csv")
    df[["긍정", "중립", "부정"]] = df[["긍정", "중립", "부정"]] / 100
    return df


@st.cache_data(show_spinner=False)
def load_news_overall_summary() -> pd.DataFrame:
    """News_Scraping_summary.csv — 정책 구분 없는 전체 전/후 감정 비율(0~100%) 1쌍."""
    df = _read_csv("News_Scraping_summary.csv")
    df[["긍정", "중립", "부정"]] = df[["긍정", "중립", "부정"]] / 100
    return df


def apt_files_missing() -> list[str]:
    return [name for name in APT_FILES if not (DATA_DIR / name).exists()]


def news_files_missing() -> list[str]:
    return [name for name in NEWS_FILES if not (DATA_DIR / name).exists()]


def guard_apt_or_stop():
    """부동산 데이터가 없으면 안내 메시지를 띄우고 멈춘다 (메인 대시보드·지역별 변동률·정책 전후 비교)."""
    missing = apt_files_missing()
    if missing:
        st.error(
            "이 화면은 부동산 거래 데이터가 있어야 합니다. data/ 폴더에 다음 파일이 아직 없습니다: "
            + ", ".join(missing)
            + "\n\nmain/dataanalysis 브랜치 파이프라인 산출물이 올라오면 자동으로 채워집니다."
        )
        st.stop()


def guard_news_or_stop():
    """뉴스 데이터가 없으면 안내 메시지를 띄우고 멈춘다 (뉴스·여론 분석)."""
    missing = news_files_missing()
    if missing:
        st.error(
            "이 화면은 뉴스 데이터가 있어야 합니다. data/ 폴더에 다음 파일이 아직 없습니다: "
            + ", ".join(missing)
            + "\n\nwebscraping 브랜치 파이프라인 산출물이 올라오면 자동으로 채워집니다."
        )
        st.stop()
