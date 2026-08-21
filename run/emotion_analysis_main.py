"""
이 파일은 수집된 뉴스 기사에 대한 Qwen 감성 분석 및 라벨링을 단독 실행하는 메인 제어 스크립트입니다.
Qwen 8B LLM 모델을 로드하여 각 뉴스 제목의 감정을 분석하고, 요약 통계 결과(summary)까지 함께 도출합니다.
실행 방법: python run/emotion_analysis_main.py --input data/News_Scraping_retouch.csv --output data/News_Scraping_retouch_qwen.csv --sample
"""

import sys
import os
import argparse

# 상위 디렉토리(루트)를 모듈 검색 경로에 추가하여 lib 패키지 로드 지원
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.analyzer import run_qwen_analysis_pipeline

def main():
    parser = argparse.ArgumentParser(description="뉴스 기사 감성 분석 실행기 (Qwen 8B LLM)")
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
        help="감성 분석 완료 결과를 저장할 CSV 파일 경로"
    )
    parser.add_argument(
        "--summary", 
        type=str, 
        default="data/News_Scraping_retouch_qwen_summary.csv", 
        help="감성 분석 전/후 통계 요약을 저장할 CSV 파일 경로"
    )
    parser.add_argument(
        "--sample", 
        action="store_true", 
        help="샘플 모드 활성화 (상위 100건만 빠르게 테스트)"
    )
    
    args = parser.parse_args()
    
    print("=============================================================")
    print(" [Qwen LLM 기반 부동산 뉴스 감성 라벨링]")
    print("=============================================================")
    print(f" 입력 파일: {args.input}")
    print(f" 출력 파일: {args.output}")
    print(f" 요약 파일: {args.summary}")
    print(f" 샘플 분석 작동 여부: {args.sample}")
    print("-------------------------------------------------------------")
    
    # 감성 분석 파이프라인 수행
    try:
        run_qwen_analysis_pipeline(
            input_path=args.input,
            output_path=args.output,
            summary_path=args.summary,
            sample_mode=args.sample
        )
    except Exception as e:
        print(f"\n[Error] 감성 분석 중 치명적인 오류가 발생했습니다: {e}")
        sys.exit(1)
        
    print("\n[Complete] Qwen 감성 분석 및 요약 CSV 생성이 완료되었습니다.")

if __name__ == "__main__":
    main()
