"""
이 파일은 라벨링된 뉴스 감성 데이터를 분석하여 통계 수치 출력 및 차트 이미지를 생성하는 메인 스크립트입니다.
대책 시행 전/후 통계 변화 지표(Delta)를 계산하고, 지정 날짜 상위 5순위 뉴스를 조회하며,
감정 추이 그래프와 비교 막대 차트를 생성하여 이미지 파일로 저장합니다.
실행 방법: python sentiment_analysis_main.py --input data/News_Scraping_retouch_qwen.csv
"""

import os
import sys
import argparse
import pandas as pd

# lib 패키지 참조를 위한 라이브러리 경로 확인
from lib.load import load_emotion_data
from lib.sentiment import calculate_metrics, get_top_news_by_date
from lib.visualization import generate_trend_chart, generate_comparison_bar_chart

def main():
    parser = argparse.ArgumentParser(description="부동산 뉴스 감성 통계 분석 및 시각화 생성기")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/News_Scraping_retouch_qwen.csv", 
        help="감성 분석 완료 결과를 담은 CSV 파일 경로"
    )
    parser.add_argument(
        "--trend-output", 
        type=str, 
        default="images/emotion_trend_qwen.png", 
        help="생성할 감정 추이 선 그래프 이미지 경로"
    )
    parser.add_argument(
        "--comparison-output", 
        type=str, 
        default="images/emotion_comparison_qwen.png", 
        help="생성할 감정 비율 비교 막대 그래프 이미지 경로"
    )
    parser.add_argument(
        "--effective-date1", 
        type=str, 
        default="2025-06-28", 
        help="첫 번째 대책 시행일 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--effective-date2", 
        type=str, 
        default="2025-09-07", 
        help="두 번째 대책 시행일 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--effective-date3", 
        type=str, 
        default="2025-10-15", 
        help="세 번째 대책 시행일 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--target-date", 
        type=str, 
        default="2025-06-28", 
        help="상위 뉴스를 조회할 기준 날짜 (YYYY-MM-DD)"
    )
    
    args = parser.parse_args()
    
    print("=============================================================")
    print(" [뉴스 감성 통계 분석 및 시각화 작업 시작]")
    print("=============================================================")
    print(f" 입력 파일: {args.input}")
    print(f" 시행일1 기준: {args.effective_date1}")
    print(f" 뉴스 조회 타겟: {args.target_date}")
    print("-------------------------------------------------------------")
    
    # 1. 데이터 로드
    try:
        df = load_emotion_data(args.input)
        print(f"[Info] 데이터 로드 성공. 기사 건수: {len(df)}개")
    except Exception as e:
        print(f"[Error] 데이터 로드 실패: {e}")
        sys.exit(1)
        
    # 2. 변화 지표(Delta) 통계 계산
    metrics = calculate_metrics(df, effective_date=args.effective_date1)
    print("\n>>> 대책 시행 전/후 감성 비율 비교 지표 (Delta):")
    print(f"  * 긍정 비율: {metrics['before_pos']:.2f}% -> {metrics['after_pos']:.2f}% (증감 Delta: {metrics['delta_pos']:.2f}%p)")
    print(f"  * 부정 비율: {metrics['before_neg']:.2f}% -> {metrics['after_neg']:.2f}% (증감 Delta: {metrics['delta_neg']:.2f}%p)")
    print(f"  * 중립 비율: {metrics['before_neu']:.2f}% -> {metrics['after_neu']:.2f}% (증감 Delta: {metrics['delta_neu']:.2f}%p)")
    print("-" * 60)
    
    # 3. 특정 날짜 감정 신뢰도 상위 기사 조회
    top_news = get_top_news_by_date(df, target_date=args.target_date, top_n=5)
    print(f"\n>>> 타겟 날짜 ({args.target_date}) 감정 신뢰도 상위 5개 기사:")
    if top_news.empty:
        print("  - 해당 날짜에 데이터가 존재하지 않습니다.")
    else:
        for idx, row in enumerate(top_news.itertuples(), 1):
            print(f"  {idx}위. {row.기사제목}")
            print(f"       * 감정 분류: {row.감정} (신뢰도: {row.수치:.4f})")
            print(f"       * 원문 URL: {row.url}")
            print(f"       * 분류 근거: {row.분류근거}")
            print("-" * 50)
            
    # 4. 이미지 저장 디렉토리 생성
    for path in [args.trend_output, args.comparison_output]:
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            
    # 5. 감정 추이 선 그래프 생성 및 저장
    try:
        import matplotlib.pyplot as plt
        fig_trend = generate_trend_chart(
            df, 
            interval_days=5, 
            effective_date1=args.effective_date1,
            effective_date2=args.effective_date2,
            effective_date3=args.effective_date3
        )
        plt.figure(fig_trend.number)
        plt.savefig(args.trend_output, dpi=150)
        plt.close(fig_trend)
        print(f"\n[Success] 감정 추이 선 그래프 저장 완료 -> {args.trend_output}")
    except Exception as e:
        print(f"[Warning] 감정 추이 선 그래프 생성 중 에러 발생: {e}")
        
    # 6. 감정 비율 비교 막대 그래프 생성 및 저장
    try:
        fig_comparison = generate_comparison_bar_chart(
            df, 
            effective_date1=args.effective_date1,
            effective_date2=args.effective_date2,
            effective_date3=args.effective_date3,
            policy_name1="6·27 가계부채 관리 강화방안",
            policy_name2="9·7 부동산 대책",
            policy_name3="10·15 부동산 대책"
        )
        plt.figure(fig_comparison.number)
        plt.savefig(args.comparison_output, dpi=150)
        plt.close(fig_comparison)
        print(f"[Success] 감정 비율 비교 막대 그래프 저장 완료 -> {args.comparison_output}")
    except Exception as e:
        print(f"[Warning] 감정 비율 비교 막대 그래프 생성 중 에러 발생: {e}")
        
    print("\n[Complete] 뉴스 감성 분석 시각화 및 지표 연산업이 모두 완료되었습니다.")

if __name__ == "__main__":
    main()
