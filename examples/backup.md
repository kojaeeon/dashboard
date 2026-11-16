---
title: KJA_샘플프로젝트
project:
  root: deploy-demo
  exclude:
    - .git/**
    - .venv/**
    - node_modules/**
    - __pycache__/**
backup:
  directory: ../data/backups
  scope: all
files:
  - source: src/main/resources/mappers/HelloMapper.xml
  - source: src/main/webapp/js/hello.js
rules:
  - name: java
    root: src/main/java
    include: ["**/*.java"]
  - name: class
    root: target/classes
    include: ["**/*.class"]
  - name: sql
    root: src/main/resources
    include: ["**/*.sql", "mappers/**/*.xml"]
  - name: js
    root: src/main/webapp
    include: ["**/*.js"]
    exclude: ["**/*.xfdl.js"]
  - name: xfdl
    root: src/main/webapp
    include: ["**/*.xfdl", "**/*.xfdl.js"]
---

# 백업 설정 예시

상대 경로는 이 MD 파일의 폴더 기준입니다. 화면의 **설정 기준 폴더**에서 확인하세요.

- **프로젝트 전체**: 프로젝트 아래 파일을 수집하고 `project.exclude`는 제외합니다.
- **지정 파일**: `files`의 `source`에 적은 파일만 백업합니다.
- **유형별 전체**: 선택한 `rules`의 root/include/exclude에 맞는 파일을 백업합니다.

모든 범위에서 ZIP 내부 경로는 프로젝트 상대 경로를 유지합니다.
백업 폴더가 프로젝트 내부에 있어도 기존 ZIP은 수집하지 않습니다.
`**/*.class`는 내부 클래스도 포함합니다. MyBatis Mapper XML도 규칙에 포함하세요.

## 실행

1. 설정 적용 후 백업 범위를 선택합니다.
2. **계획 만들기**에서 파일 목록과 백업 폴더를 확인합니다.
3. **ZIP 백업 실행**을 누릅니다. 백업 ZIP과 실행 결과 JSON을 다운로드할 수 있습니다.

ZIP 이름은 `title_YYYYMMDD_HHMMSS_ffffff.zip`이며 한국 시간입니다.
계획 후 원본이 바뀌면 실패한 ZIP을 삭제하고 재계획을 요청합니다.
결과는 `data/backup_runs/<실행 ID>/result.json`에 기록됩니다.

기존 MD의 `deploy`, `files.target`, `rules.target`은 백업에 사용하지 않습니다.
