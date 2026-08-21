"""
이 파일은 3관점 감성 분석 데이터를 바탕으로 관점별 감정 트렌드 차트를 생성하고 저장하는 시각화 모듈입니다.
Matplotlib을 이용하여 각 관점(기업, 소비자, 시장)의 5일 단위 일평균 감정 추이 선 그래프를 생성하고,
주요 부동산 대책(6·27, 9·7, 10·15)의 시행일을 수직선으로 나타냅니다.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def generate_3view_trend_chart(input_csv_path, output_image_path):
    """
    기업/소비자/시장 각 관점별로 5일 단위 일평균 감정 추세를 꺾은선 그래프로 시각화하고 저장합니다.
    """
    if not os.path.exists(input_csv_path):
        raise FileNotFoundError(f"[Error] 시각화할 입력 파일 '{input_csv_path}'이(가) 존재하지 않습니다.")
        
    # 한글 폰트 설정 (Windows 기본 맑은 고딕 우선 적용)
    plt.rc('font', family='Malgun Gothic')
    plt.rc('axes', unicode_minus=False)
    
    df_viz = pd.read_csv(input_csv_path, encoding="utf-8-sig")
    df_viz['날짜'] = pd.to_datetime(df_viz['날짜'])
    
    dir_name = os.path.dirname(output_image_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
        
    # 3개 대책 시행일 및 라벨 정의
    policy_dates = [
        (pd.to_datetime('2025-06-28'), '6·27'),
        (pd.to_datetime('2025-09-08'), '9·7'),
        (pd.to_datetime('2025-10-16'), '10·15')
    ]
    
    viewpoints = ['기업', '소비자', '시장']
    colors = {'부정': '#e74c3c', '중립': '#95a5a6', '긍정': '#2ecc71'}
    
    fig, axes = plt.subplots(3, 1, figsize=(16, 18), sharex=True)
    
    for i, vp in enumerate(viewpoints):
        col_name = f'{vp}_감정'
        
        # 날짜별 감정 빈도 집계
        df_daily = df_viz.groupby(['날짜', col_name]).size().unstack(fill_value=0)
        for col in ['긍정', '중립', '부정']:
            if col not in df_daily.columns:
                df_daily[col] = 0
                
        all_dates = pd.date_range(start=df_daily.index.min(), end=df_daily.index.max(), freq='D')
        df_daily = df_daily.reindex(all_dates, fill_value=0)
        
        # 5일 단위 리샘플링 및 평균 산출
        df_5d = df_daily.resample('5D').mean()
        
        ax = axes[i]
        for col in ['부정', '중립', '긍정']:
            ax.plot(df_5d.index, df_5d[col], marker='o', linewidth=1.8, markersize=4, color=colors[col], label=col, alpha=0.85)
            
        # 3개 대책 시행일 수직선 표시
        for j, (dt, label) in enumerate(policy_dates):
            ax.axvline(x=dt, color='#3498db', linestyle='--', linewidth=2,
                       label=f'대책 시행일 ({dt.strftime("%Y-%m-%d")})' if i == 0 else '', alpha=0.8)
            
        # x축 포맷 및 눈금 설정 (5일 단위)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        ax.set_title(f'[{vp} 관점] 부동산 대책 시행 전후 감정 추이 (5일 단위 일평균)', fontsize=14, fontweight='bold', pad=12)
        ax.set_ylabel('일평균 뉴스 기사 수 (건)', fontsize=11)
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.legend(loc='upper right', fontsize=9)
        
    axes[-1].set_xlabel('날짜', fontsize=11, labelpad=8)
    plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45, ha='right')
    plt.tight_layout()
    
    plt.savefig(output_image_path, dpi=150)
    plt.close()
    print(f"[Success] 3관점 감정 트렌드 차트 저장 완료 -> {output_image_path}")
