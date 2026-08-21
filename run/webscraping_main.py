"""
이 파일은 네이버 부동산 뉴스 크롤링을 단독 실행하는 메인 제어 스크립트입니다.
지정한 파일 경로에 크롤링된 부동산 뉴스 기사 목록을 저장합니다.
실행 방법: python run/webscraping_main.py --output data/News_Scraping_retouch.csv --max-articles 100
"""

import sys
import os
import argparse

# 상위 디렉토리(루트)를 모듈 검색 경로에 추가하여 lib 패키지 로드 지원
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.crawler import scrape_all_policies

def main():
    parser = argparse.ArgumentParser(description="네이버 부동산 뉴스 크롤러 실행기")
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/News_Scraping_retouch.csv", 
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
    print(" [부동산 뉴스 스크래퍼 실행]")
    print("=============================================================")
    print(f" 저장 파일: {args.output}")
    print(f" 하루 기사 한도: {args.max_articles}개")
    print("-------------------------------------------------------------")
    
    # 크롤링 시작
    scrape_all_policies(filename=args.output, max_articles_per_day=args.max_articles)
    
    print("\n[Complete] 뉴스 수집 크롤링 작업이 성공적으로 종료되었습니다.")

if __name__ == "__main__":
    main()
