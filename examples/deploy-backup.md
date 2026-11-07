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
    target: WEB-INF/classes/mappers/HelloMapper.xml
  - source: src/main/webapp/js/hello.js
    target: js/hello.js
rules:
  - name: java
    root: src/main/java
    include: ["**/*.java"]
    target: src/main/java
  - name: class
    root: target/classes
    include: ["**/*.class"]
    target: WEB-INF/classes
  - name: sql
    root: src/main/resources
    include: ["**/*.sql", "mappers/**/*.xml"]
    target: WEB-INF/classes
  - name: js
    root: src/main/webapp
    include: ["**/*.js"]
    exclude: ["**/*.xfdl.js"]
    target: .
  - name: xfdl
    root: src/main/webapp
    include: ["**/*.xfdl", "**/*.xfdl.js"]
    target: .
deploy:
  method: copy
  target_root: ../data/deploy-demo
  scope: categories
  categories: [class, sql, js, xfdl]
  overwrite: true
---

# 배포/백업 설정 예시

처음에는 동봉된 `deploy-demo` 프로젝트와 `data/deploy-demo` 복사 대상을 사용합니다.
실제 프로젝트에 쓰려면 프론트메터의 원본·대상 경로를 바꾸세요.
상대 경로는 이 MD 파일이 있는 폴더 기준입니다. 화면의 **설정 기준 폴더**에서 확인합니다.

## 처리 범위

- **전체**: 프로젝트 아래 모든 파일을 상대 경로 그대로 처리합니다. `project.exclude`는 제외합니다.
- **파일별**: `files`의 `source`를 읽어 `target`으로 복사합니다.
- **유형별**: 선택한 `rules`의 파일을 수집하며, 각 `root` 기준 상대 경로를 `target` 아래에 유지합니다.

`**/*.class`는 루트 및 하위 디렉터리를 모두 포함하므로 Java 내부 클래스(`$...class`)도 수집합니다.
MyBatis는 `.sql`뿐 아니라 실제 Mapper `.xml`도 규칙에 포함하세요.
JS 규칙에서 `.xfdl.js`를 제외해 XFDL 규칙과의 중복을 방지했습니다.
실제 서버가 생성된 `.xfdl.js`만 사용한다면 XFDL 규칙의 `.xfdl`을 제거하세요.

## Java 배포

Java 소스를 전송하는 것과 실행용 빌드 결과를 전송하는 것은 다릅니다.
`java` 유형은 `.java` 소스, `class` 유형은 빌드된 `.class` 파일입니다.
기본 배포 선택은 `class`이며 `target/classes`의 내부 클래스도 포함합니다.
Gradle 프로젝트라면 `build/classes/java/main` 같은 실제 빌드 경로로 수정하세요.
선택한 Java 파일만 처리하려면 유형 규칙을 `demo/Hello*.class`로 좁히면 내부 클래스도 함께 선택됩니다.
서버가 실행형 Spring Boot JAR를 사용하면 개별 class 대신 JAR 파일을 매핑하세요.
대시보드는 파일을 전송하며 Java 빌드, SQL 실행, 서버 재시작은 수행하지 않습니다.

```yaml
# 실행형 Spring Boot JAR 예시: 필요한 경우 deploy.categories에 artifact를 선택
rules:
  - name: artifact
    root: target
    include: ["myapp.jar"]
    target: .
```

## ZIP과 복사

백업은 `title_YYYYMMDD_HHMMSS_ffffff.zip` 형식으로 생성합니다. 날짜는 한국 시간입니다.
백업 ZIP에는 프로젝트 상대 경로를 유지합니다.
배포 시에도 보낼 내용을 같은 형식의 ZIP으로 먼저 고정한 후 그 ZIP의 파일을 전송합니다.
배포 대상 서버의 기존 파일은 백업하지 않습니다. ZIP은 로컬 원본 파일만 담습니다.
계획 후 원본이나 로컬 대상이 바뀌면 계획을 다시 만들어야 합니다.
전송이 중간에 실패하면 완료된 파일은 유지되고 이후 파일은 건너뜁니다. 결과의 파일별 완료 상태를 확인하세요.

## FTP 배포

다음처럼 `deploy`를 바꾸면 동일한 파일 계획을 FTP로 전송합니다.
비밀번호는 MD에 쓰지 않고 지정한 환경변수 또는 앱의 `.env`에서 읽습니다.

```yaml
deploy:
  method: ftp
  target_root: /apps/myapp
  scope: categories
  categories: [class, sql, js, xfdl]
  overwrite: true
  ftp:
    host: ftp.example.internal
    port: 21
    username: deploy-user
    password_env: DEPLOY_FTP_PASSWORD
    tls: false
    passive: true
    timeout: 30
    encoding: utf-8
```

FTP 계정에는 대상 목록 조회, 업로드·이름 변경·임시 파일 정리 권한이 필요합니다.
서버의 기존 파일은 내려받지 않으며 임시 이름으로 업로드하고 최종 이름으로 전환합니다.
FTP는 SFTP와 다른 프로토콜이며, 이 메뉴는 FTP와 명시적 FTPS(`tls: true`)를 지원합니다.


## 타깃 루트 기준 상대 경로

`deploy.target_root`를 화면의 **배포 타깃 루트**에 읽어옵니다. 화면에서 바꾼 뒤 계획을 다시 만들 수 있습니다.
`files.target`과 `rules.target`은 항상 이 루트 아래의 상대 경로입니다.
예를 들어 루트가 `/apps/myapp`이고 target이 `WEB-INF/classes/demo/Hello.class`라면
실제 경로는 `/apps/myapp/WEB-INF/classes/demo/Hello.class`입니다.
계획에는 대상 상대 경로와 실제 대상 경로가 함께 표시됩니다.
기존 문서의 `deploy.destination`도 타깃 루트로 읽습니다.
