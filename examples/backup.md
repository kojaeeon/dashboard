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
  scope: files
files:
  - source: src/main/resources/mappers/HelloMapper.xml
    target: /srv/app/mappers/HelloMapper.xml
  - source: src/main/webapp/js/hello.js
    target: /srv/app/js/hello.js
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

기존 MD의 `deploy`, `files.target`, `rules.target`은 ZIP 백업에 사용하지 않습니다.

## FTP COPY (SFTP 전송)

프론트메터에 아래 `sftp` 항목을 추가한 후 **FTP COPY**를 누릅니다.
백업 범위와 관계없이 `files`의 모든 `source`를 해당 `target`으로 업로드합니다.
`source`는 프로젝트 기준 상대 파일 경로, `target`은 원격 파일 경로입니다.
원격 상위 폴더는 자동 생성하고 같은 이름의 파일은 덮어씁니다.
전송은 순서대로 진행하며 오류가 발생하면 중단합니다. 이미 전송된 파일은 유지됩니다.

```yaml
sftp:
  host: sftp.example.com
  port: 22
  username: deploy
  password: "서버 비밀번호"
  # private_key: ~/.ssh/id_ed25519  # 비밀번호 대신 개인 키 사용 가능
  # passphrase: "개인 키 암호"
  # known_hosts: ~/.ssh/known_hosts
  timeout: 30
```

개인 키와 known_hosts의 상대 경로는 설정 기준 폴더에서 해석합니다.
서버 호스트 키는 기본 `~/.ssh/known_hosts` 또는 지정한 `known_hosts`에 등록되어 있어야 합니다.
접속 정보는 MD에서만 읽으며 전송 결과 JSON에 비밀번호와 개인 키 암호를 저장하지 않습니다.
실제 접속 정보를 넣은 문서는 버전 관리에서 제외하세요.
