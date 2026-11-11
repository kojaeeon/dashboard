---
browser: chromium
executable_path: 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
headless: false
viewport:
  width: 1920
  height: 1080
timeout: 15000
---

# 브라우저 설정

UI_TEST의 브라우저 설정 MD에서 선택하거나 업로드합니다.
`chromium` 엔진으로 기존 Edge 실행 파일을 사용합니다.
실행 PC의 실제 경로로 수정하세요. YAML에서 Windows 경로는 작은따옴표로 감쌉니다.
`executable_path`를 생략하면 Playwright가 설치한 해당 브라우저를 사용합니다.
시작 URL은 시나리오의 `browser.base_url`을 유지하며 실행 화면에서 변경할 수 있습니다.
MD의 `headless`는 브라우저 표시 스위치에 반영됩니다. 스위치를 직접 변경하면 그 값으로 실행합니다.
