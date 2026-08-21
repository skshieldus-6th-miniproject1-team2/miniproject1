"""
이 파일은 수집된 뉴스 기사에 대해 3가지 관점(기업, 소비자, 시장)의 감정 분석 및 트렌드 시각화를 일괄 실행하는 메인 제어 스크립트입니다.
pandas 벡터화 기법을 사용하여 감정을 일괄 분류하고, 요약 CSV 통계와 시각화 이미지(png)를 차례로 도출합니다.
실행 방법: python run/j_emotion_analysis_main.py --input data/News_Scraping_retouch.csv --output data/News_Scraping_retouch_qwen.csv --summary data/News_Scraping_retouch_qwen_summary.csv --trend-output images/emotion_trend_qwen.png
"""

import sys
import os
import argparse

# 루트 디렉토리를 모듈 검색 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.j_analyzer import run_qwen_analysis_pipeline_3view
from lib.j_visualization import generate_3view_trend_chart

def main():
    parser = argparse.ArgumentParser(description="3관점 뉴스 기사 감성 분석 및 시각화 실행기")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/News_Scraping_retouch.csv", 
        help="크롤링 수집된 뉴스 원본 CSV 파일 경로"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/News_Scraping_retouch_qwen.csv", 
        help="3관점 감성 분석 완료 결과를 저장할 CSV 파일 경로"
    )
    parser.add_argument(
        "--summary", 
        type=str, 
        default="data/News_Scraping_retouch_qwen_summary.csv", 
        help="대책별 3관점 분석 통계 요약을 저장할 CSV 파일 경로"
    )
    parser.add_argument(
        "--trend-output", 
        type=str, 
        default="images/J_emotion_trend_qwen.png", 
        help="생성할 3관점 감정 추이 선 그래프 이미지 경로"
    )
    parser.add_argument(
        "--sample", 
        action="store_true", 
        help="샘플 모드 활성화 (상위 100건만 빠르게 테스트)"
    )
    
    args = parser.parse_args()
    
    print("=============================================================")
    print(" [3관점 부동산 뉴스 감성 라벨링 및 시각화 파이프라인]")
    print("=============================================================")
    print(f" 입력 파일: {args.input}")
    print(f" 출력 파일: {args.output}")
    print(f" 요약 파일: {args.summary}")
    print(f" 차트 파일: {args.trend_output}")
    print(f" 샘플 분석 여부: {args.sample}")
    print("-------------------------------------------------------------")
    
    # 1. 3관점 감성 분석 및 요약 CSV 생성 실행
    try:
        run_qwen_analysis_pipeline_3view(
            input_path=args.input,
            output_path=args.output,
            summary_path=args.summary,
            sample_mode=args.sample
        )
    except Exception as e:
        print(f"\n[Error] 감성 분석 파이프라인 수행 중 오류 발생: {e}")
        sys.exit(1)
        
    # 2. 3관점 트렌드 시각화 저장 실행
    try:
        print(f"\n[Start] 3관점 감정 추이 시각화 차트 생성을 시작합니다...")
        generate_3view_trend_chart(
            input_csv_path=args.output,
            output_image_path=args.trend_output
        )
    except Exception as e:
        print(f"\n[Warning] 3관점 트렌드 시각화 생성 중 에러 발생: {e}")
        
    print("\n[Complete] 3관점 뉴스 감성 분석 및 시각화 파이프라인이 성공적으로 종료되었습니다.")

if __name__ == "__main__":
    main()
