# code_gen 메뉴

## MD에서 자동 입력

화면 상단의 `프론트매터 MD 선택`은 MD 보기에서 저장한 문서와 등록된 로컬 폴더(하위 폴더 포함)의 MD를 표시합니다. 새 문서/파일은 목록 새로고침으로 반영합니다. 로컬 파일은 UTF-8이며 2MB 이하를 지원합니다.

사진의 기존 업무 문서 키를 그대로 사용합니다.

```yaml
---
workItem:
  table: "KAML.CDD_BC1_INQRY_DOC"
  service: "CddBc1Qry"
  serviceNm: "BC1질의서"
  package: "com.kaml.cdd"
---
```

`table` → 테이블명, `service` → 서비스명, `serviceNm` → 서비스 한글명, `package` → 패키지 경로입니다. `menu`, `workStatus`, `repo`, `deploy` 등 다른 키는 읽어도 생성 입력에는 반영하지 않습니다. 생성 대상 체크박스는 현재 선택을 유지합니다.

문서를 선택하면 네 필드를 모두 검증한 뒤 자동 입력하며 기존 생성 결과와 ZIP 다운로드를 초기화합니다. 입력값은 직접 수정할 수 있고 코드 생성은 미리보기 버튼으로 실행합니다. `직접 입력`은 콤보 선택을 지우면 됩니다. YAML 오류/필수 키 누락 시 기존 입력값은 유지하고 오류를 표시합니다. 생성 서비스(`app/codegen/service.py`)는 수정하지 않았습니다.

`app/pages/code_gen.py`가 화면을 구성합니다. 생성 파일 헤더 오른쪽 다운로드 아이콘은 현재 미리보기 결과 전체를 UTF-8 ZIP으로 다운로드합니다. ZIP에는 프로젝트 상대 경로가 유지됩니다. 입력값이나 생성 대상이 바뀌면 이전 결과와 다운로드를 비워 다시 미리보기를 실행하도록 합니다.

현재 `PreviewGenerator`는 화면 확인용 Jinja2 샘플만 렌더링합니다. DB 메타 조회, 실제 SQL 및 업무 코드는 구현하지 않았습니다. 화면 최초 진입 시 자동 생성하지 않습니다.

## 실제 서비스 연결

`app/codegen/service.py`의 계약을 사용합니다.

```python
from app.codegen.service import GenerationRequest, GeneratedFile

class MyCodeGenerator:
    def generate(self, request: GenerationRequest) -> list[GeneratedFile]:
        request.validate()
        # request.table_name: 스키마.테이블 또는 테이블명
        # request.service_name: 영문 대문자로 시작하는 클래스명
        # request.service_korean_name: 서비스 한글명
        # request.package_path: com.example.service
        # request.targets: Controller / Service / VO / Mapper 선택값
        # 여기서 DB 메타 조회 및 사용자 Jinja2 템플릿 렌더링
        return [GeneratedFile(
            path='src/main/java/com/example/ExampleVO.java',
            content='package com.example;\npublic class ExampleVO {}\n',
            language='java',
        )]
```

`app/main.py`에서 주입합니다.

```python
with ui.tab_panel(code_gen_tab).classes('p-0'):
    code_gen.render(db, generator=MyCodeGenerator())
```

`generate()`는 동기 함수이며 UI가 `run.io_bound()`로 실행합니다. 서비스 내부에서는 NiceGUI UI를 조작하지 않고 결과만 반환하세요. DB 연결이 필요하면 메서드 내부에서 열고 닫으세요. 빈 결과 또는 잘못된 파일 경로는 오류로 표시됩니다. `language`는 NiceGUI 코드 미리보기 언어이며 XML은 `xml`을 사용합니다.

## 실행 및 검증

```bash
python -m pip install -e '.[dev]'
python -m pytest tests/test_codegen.py -q
python -m app.main
```

서버가 `reload=False`로 실행되므로 수정 후 재시작해야 합니다.
