---
title: KJA_BOARD 기본 UI 흐름
workItem:
  serviceNm: 대시보드 메뉴 및 목차 확인
  menu: MD 보기 > Work > UI_TEST
browser:
  base_url: http://127.0.0.1:8080
  timeout: 10000
  headless: false
step:
  - action: assert_visible
    text: Markdown Workspace
  - action: click
    role: button
    name: 문서 목차 열기
  - action: assert_visible
    text: 문서 목차 · Index
  - action: click
    role: button
    name: 목차 닫기
  - action: menu
    role: tab
    name: Work
  - action: assert_visible
    role: button
    name: 작업 추가
  - action: menu
    role: tab
    name: UI_TEST
  - action: assert_visible
    role: button
    name: 테스트 실행
  - action: screenshot
---

# KJA_BOARD UI 테스트

`workItem`에는 업무 정보를, `step`에는 실행할 순서를 작성합니다.
본문은 사람이 읽는 테스트 설명이며 실행 명령으로 해석하지 않습니다.
이 예시는 문서 목차와 세 메뉴를 확인하며 문서나 작업을 변경하지 않습니다.

## 작성 규칙

- `menu`, `click`, `dblclick`: 지정한 대상을 클릭합니다.
- `text` / `fill`: `label` 또는 `selector`로 찾은 입력란에 `value`를 입력합니다.
- `select`: HTML select의 option value를 지정합니다. 커스텀 콤보는 클릭 단계로 표현합니다.
- `check`, `uncheck`, `press`: 체크박스 또는 키보드를 조작합니다.
- `assert_visible`, `assert_text`: 보임 여부 또는 `value` 문자열 포함 여부를 검증합니다.
- `wait`: 대상이 보일 때까지 기다립니다. 고정 지연 대신 사용합니다.
- `goto`: `url`로 이동합니다. 상대 주소는 `browser.base_url` 기준입니다.
- `popup`: 새 창을 여는 대상을 클릭하고 이후 단계를 새 창에서 실행합니다.
- `frame`: `selector`에 해당하는 iframe 안으로 전환합니다. `main_frame`으로 돌아옵니다.
- `screenshot`: 해당 단계의 화면을 PNG로 저장합니다.

## 요소 찾기

`selector`, `id`, `attr`, `syscode`, `role`은 지정한 조건으로 찾습니다.
`role`의 표시 이름은 `name` 또는 `label`을 사용합니다.
그 외에는 `label`로 접근성 라벨을 우선 찾고, 같은 텍스트로 찾습니다.
보이는 대상이 여러 개라면 `selector`로 좁히거나 `nth: 0`처럼 순번을 지정하세요.
클릭 실패 후 다른 요소를 재클릭하지 않으며 첫 실패에서 나머지 단계는 건너뜁니다.

```yaml
# 예시: 입력과 클릭
step:
  - action: text
    label: 고객번호
    value: "00123456"
  - action: click
    role: button
    name: 조회
  - action: assert_text
    selector: "#result"
    value: 조회 완료
```
