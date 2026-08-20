---
trigger: model_decision
description: 새로운 폴더를 생성하고 만들 때 다음 규칙을 사용합니다
---

- 가상환경 설정과 모든 패키지 설치와 실행은 uv만 사용합니다. 
- conda, poetry, pipenv, virtualenv, python -m venv는 사용하지 않습니다.
- 가상환경은 워크스페이스 루트의 .venv 하나만 사용합니다.
- 새 프로젝트 폴더를 만들어도 별도 가상환경을 만들지 말고 공통 .venv를 사용합니다.
- 새 프로젝트 폴더를 만들면 내부에 images, docs, src, data 폴더를 자동으로 생성합니다.
- images는 시각화 이미지 저장, docs는 문서 저장, src는 Source Code 파일 저장, data는 데이터 파일 저장 용도로 사용합니다.

기본 구조 예시

workspace/
  .venv/
  project-a/
    images/
    docs/
    src/
    data/
  project-b/
    images/
    docs/
    src/
    data/

새 프로젝트 생성 요청 시에는 다음 원칙으로 작업합니다.
- 워크스페이스 루트의 .venv 존재 여부를 확인합니다.
- 지정한 프로젝트 폴더와 그 안의 images, docs, src, data 폴더를 생성합니다.
- 이후 작업은 모두 공통 .venv를 기준으로 진행합니다.