"""
이 파일은 뉴스 감성 분석 시각화 차트를 생성하는 모듈입니다.
Matplotlib을 활용하여 대책 시행 전후 감정 변화 추이 꺾은선 그래프 및
시행 전/후 감정 비율을 비교하는 막대 그래프를 생성합니다.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from lib.theme import (
    COLOR_EMO_POSITIVE,
    COLOR_EMO_NEUTRAL,
    COLOR_EMO_NEGATIVE,
    setup_matplotlib_font
)

# 차트 한글 깨짐 방지 폰트 초기화 설정
setup_matplotlib_font()

def generate_trend_chart(df, interval_days=5, effective_date1="2025-06-28", effective_date2="2025-09-07", effective_date3="2025-10-15"):
    
    """
    지정된 일수 단위(interval_days) 평균으로 집계하여
    감정별 뉴스 수 추이를 꺾은선 그래프(Matplotlib Figure)로 생성합니다.
    """
    # 날짜별 감정 빈도 집계
    df_daily = df.groupby(['날짜', '감정']).size().unstack(fill_value=0)
    for col in ['긍정', '중립', '부정']:
        if col not in df_daily.columns:
            df_daily[col] = 0
            
    # 전체 날짜 축 정렬 및 리인덱스
    all_dates = pd.date_range(start=df_daily.index.min(), end=df_daily.index.max(), freq='D')
    df_daily = df_daily.reindex(all_dates, fill_value=0)
    
    # 시간 단위 리샘플링
    resample_rule = f"{interval_days}D"
    df_resampled = df_daily.resample(resample_rule).mean()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = {'긍정': COLOR_EMO_POSITIVE, '중립': COLOR_EMO_NEUTRAL, '부정': COLOR_EMO_NEGATIVE}
    
    # 각 감정 극성별 라인 플롯 생성
    for col in ['부정', '중립', '긍정']:
        ax.plot(
            df_resampled.index, 
            df_resampled[col], 
            marker='o', 
            linewidth=2.5, 
            color=colors[col], 
            label=col
        )
        
    # 대책 시행일 마커 추가
    eff_dt = pd.to_datetime(effective_date1)
    ax.axvline(
        x=eff_dt, 
        color='#3498db', 
        linestyle='--', 
        linewidth=2.5, 
        label=f'대책 시행일 ({effective_date1})'
    )

    # 대책 시행일 마커 추가
    eff_dt = pd.to_datetime(effective_date2)
    ax.axvline(
        x=eff_dt, 
        color='#3498db', 
        linestyle='--', 
        linewidth=2.5, 
        label=f'대책 시행일 ({effective_date2})'
    )

    # 대책 시행일 마커 추가
    eff_dt = pd.to_datetime(effective_date3)
    ax.axvline(
        x=eff_dt, 
        color='#3498db', 
        linestyle='--', 
        linewidth=2.5, 
        label=f'대책 시행일 ({effective_date3})'
    )
    
    # x축 날짜 포맷 설정
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval_days))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    ax.set_title(f'부동산 대책 시행 전후 감정 추이 ({interval_days}일 단위 일평균)', fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel('날짜', fontsize=11)
    ax.set_ylabel('일평균 뉴스 기사 수 (건)', fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', fontsize=10)
    plt.tight_layout()
    
    return fig

def generate_comparison_bar_chart(df, 
                                  effective_date1="2025-06-28", 
                                  effective_date2="2025-09-07", 
                                  effective_date3="2025-10-15",
                                  policy_name1="6·27 가계부채 관리 강화방안",
                                  policy_name2="9·7 부동산 대책",
                                  policy_name3="10·15 부동산 대책"):
    """
    3개의 대책 시행일 각각에 대해 전과 후의 긍정/중립/부정 점유비율(%)을 계산하여
    1행 3열 형태의 막대 차트(Matplotlib Figure)로 생성합니다.
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 6.5))
    colors = [COLOR_EMO_POSITIVE, COLOR_EMO_NEUTRAL, COLOR_EMO_NEGATIVE]
    
    dates = [effective_date1, effective_date2, effective_date3]
    names = [policy_name1, policy_name2, policy_name3]
    
    for idx, (date_str, name) in enumerate(zip(dates, names)):
        ax = axes[idx]
        eff_dt = pd.to_datetime(date_str)
        
        df_temp = df.copy()
        df_temp['period'] = df_temp['날짜'].apply(lambda x: '시행 전' if x < eff_dt else '시행 후')
        
        # 빈도수 피벗
        pivot_df = df_temp.groupby(['period', '감정']).size().unstack(fill_value=0)
        for col in ['긍정', '중립', '부정']:
            if col not in pivot_df.columns:
                pivot_df[col] = 0
                
        # 비율(%) 환산
        ratio_df = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100
        ratio_df = ratio_df.reindex(columns=['긍정', '중립', '부정'])
        ratio_df = ratio_df.reindex(['시행 전', '시행 후'])
        
        ratio_df.plot(kind='bar', stacked=False, color=colors, ax=ax, width=0.6, legend=False)
        
        ax.set_title(f"{name}\n({date_str} 시행)", fontsize=11, fontweight='bold', pad=10)
        ax.set_ylabel('비율 (%)', fontsize=10)
        ax.set_xlabel('시기', fontsize=10)
        ax.set_xticklabels(['시행 전', '시행 후'], rotation=0)
        ax.grid(axis='y', linestyle=':', alpha=0.6)
        
        # 막대 상단에 비율 텍스트 추가
        for p in ax.patches:
            height = p.get_height()
            if height > 0:
                ax.annotate(
                    f"{height:.1f}%",
                    (p.get_x() + p.get_width() / 2., height),
                    ha='center', 
                    va='bottom', 
                    fontsize=9.5, 
                    xytext=(0, 2),
                    textcoords='offset points'
                )
                
    # 단일 통합 범례 배치
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.98), ncol=3, title="감정 라벨")
    
    plt.suptitle("부동산 대책별 시행 전 vs 후 뉴스 감정 비율 (%) 비교", fontsize=15, fontweight='bold', y=1.03)
    plt.tight_layout()
    return fig
