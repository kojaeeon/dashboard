# UI_TEST 브라우저 MD

UI_TEST 오른쪽 `브라우저 MD 설정`에서 등록 폴더의 MD를 선택하거나 파일을 업로드하세요. 폴더는 MD 보기에서 등록합니다. `브라우저 설정 예시 · browser.md`를 선택하면 저장소의 예시를 읽습니다.

```yaml
---
browser: chromium
executable_path: 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
headless: false
viewport:
  width: 1920
  height: 1080
timeout: 15000
---
```

- `browser`: Playwright 엔진 이름(`chromium`, `firefox`, `webkit`). Edge 실행 파일은 `chromium` 엔진으로 실행합니다.
- `executable_path`: dashboard가 실행되는 PC의 브라우저 실행 파일 경로. 생략 시 Playwright 설치 브라우저를 사용합니다. Windows 경로는 YAML 작은따옴표로 감싸세요.
- `headless`: `false`면 브라우저 창 표시. 화면의 브라우저 표시 스위치를 바꾸면 실행 시 스위치 값을 우선합니다.
- `viewport`: 브라우저 내부 페이지 크기(px). 운영체제 창 외곽 크기는 아닙니다.
- `timeout`: 기본 동작/탐색 제한 시간(ms). 개별 step의 timeout이 있으면 해당 단계에서 우선합니다.

선택한 브라우저 MD에 명시된 키를 시나리오의 browser 설정에 덮어씁니다. 생략된 키는 시나리오 값을 유지합니다. 시작 URL은 시나리오의 `browser.base_url`을 유지하며, 실행 화면에서 직접 바꿀 수 있습니다. 선택을 지우면 시나리오 설정으로 돌아갑니다. 잘못된 브라우저 MD는 실행을 막고 오류를 표시합니다. 실행 파일이 없으면 다른 브라우저로 대체하지 않고 실패 원인을 표시합니다.

실행 폴더의 `browser.json`에는 적용된 설정이 저장됩니다. 시나리오와 브라우저 MD는 별개이므로 브라우저 MD에 step을 넣을 필요가 없습니다. 기존 시나리오 내부의 `browser: {base_url: ..., headless: ...}` 형식도 계속 지원합니다.
