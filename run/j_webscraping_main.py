"""
이 파일은 지정된 특정 기간(2025-05-23 ~ 2025-10-26)의 부동산 뉴스를 스크랩핑하는 크롤링 작업을 단독 실행하는 메인 제어 스크립트입니다.
수집된 뉴스는 지정한 CSV 파일에 중복을 제거하여 날짜별로 정렬되어 저장됩니다.
실행 방법: python run/j_webscraping_main.py --output data/j_News_Scraping_retouch.csv --max-articles 100
"""

import sys
import os
import argparse

# 루트 디렉토리를 모듈 검색 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.j_crawler import scrape_full_period

def main():
    parser = argparse.ArgumentParser(description="부동산 뉴스 스크래퍼 실행기 (J버전)")
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/j_News_Scraping_retouch.csv", 
        help="크롤링 수집 데이터를 저장할 CSV 파일 경로"
    )
    parser.add_argument(
        "--max-articles", 
        type=int, 
        default=100, 
        help="날짜별 최대 수집 기사 수 (기본값: 100)"
    )
    
    args = parser.parse_args()
    
    print("=============================================================")
    print(" [J 부동산 뉴스 스크래퍼 실행]")
    print("=============================================================")
    print(f" 저장 파일: {args.output}")
    print(f" 하루 기사 한도: {args.max_articles}개")
    print("-------------------------------------------------------------")
    
    # 크롤링 시작
    scrape_full_period(filename=args.output, max_articles_per_day=args.max_articles)
    
    print("\n[Complete] 뉴스 수집 크롤링 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()
