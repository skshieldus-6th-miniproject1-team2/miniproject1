"""
이 파일은 뉴스 감성 분석 데이터를 로드하고 전처리하는 헬퍼 함수를 포함하는 모듈입니다.
Streamlit 환경에서는 캐싱을 적용하여 성능을 최적화하고, 일반 파이썬 실행 환경에서도 정상 동작하도록 설계되었습니다.
"""

import os
import pandas as pd

# Streamlit 패키지가 설치되어 있는 경우 캐싱을 적용하고, 그렇지 않은 경우 일반 데코레이터를 적용합니다.
try:
    import streamlit as st
    cache_decorator = st.cache_data
except ImportError:
    def cache_decorator(func):
        return func

@cache_decorator
def load_emotion_data(csv_path="data/News_Scraping.csv"):
    """
    Qwen 감성 분석 완료 CSV 파일을 불러와 '날짜' 컬럼을 datetime으로 변환하고,
    '수치' 컬럼을 실수형(Float)으로 안전하게 변환하여 결측치를 보정해 반환합니다.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"감정 분석 파일({csv_path})을 찾을 수 없습니다. 경로를 확인해 주세요.")
        
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df['날짜'] = pd.to_datetime(df['날짜'])
    df['수치'] = pd.to_numeric(df['수치'], errors='coerce').fillna(0.0)
    return df
