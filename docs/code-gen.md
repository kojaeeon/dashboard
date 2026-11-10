# code_gen 메뉴

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
