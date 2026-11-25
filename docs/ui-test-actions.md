# UI_TEST 액션 가이드

**UI_TEST**에서 시나리오 MD를 선택하거나 업로드하면 `browser`와 `step`을 읽기 전용으로 미리 볼 수 있습니다. 문서 맨 위의 YAML 프론트매터에 `step` 목록을 작성한 뒤 **단계 확인**과 **테스트 실행**을 누릅니다. 단계는 위에서부터 실행되며, 첫 실패 이후의 단계는 건너뜁니다.

```yaml
---
title: 정기점검 메뉴 열기
browser:
  base_url: 'http://127.0.0.1:8080'
  timeout: 10000
step:
  - action: click
    role: button
    name: 점검
  - action: wait
    text: 정기점검
    timeout: 30000
  - action: js
    label: 페이지 제목 확인
    script: '() => document.title'
---
```

`title`과 `workItem`은 문서 정보이며 `step`은 필수입니다. `browser`는 생략할 수 있습니다. YAML에서 `#`으로 시작하는 선택자와 앞에 0이 있는 업무 코드는 따옴표로 감싸세요.

## 액션별 속성

표의 **대상**은 다음 절의 요소 찾기 속성을 뜻합니다. `label`은 실행 화면에 단계 이름으로도 표시할 수 있습니다. `goto`, `js`처럼 요소를 찾지 않는 액션에서는 표시용으로만 쓸 수 있습니다.

| `action` | 필수 속성 | 선택 속성 / 동작 | 한 줄 예시 |
|---|---|---|---|
| `goto` | `url` 또는 `value` | `timeout`. 상대 주소는 시작 URL 기준입니다. 이동 후 현재 탭의 메인 문서를 사용합니다. | `{action: goto, url: '/checks'}` |
| `menu` | 대상 | `timeout`. 메뉴 요소를 한 번 클릭합니다. | `{action: menu, text: 점검}` |
| `click` | 대상 | `timeout`. 요소를 한 번 클릭합니다. | `{action: click, role: button, name: 조회}` |
| `dblclick` | 대상 | `timeout`. 요소를 더블클릭합니다. | `{action: dblclick, text: 정기점검}` |
| `text` | 대상, `value` | `timeout`. 입력값 전체를 문자열로 바꿉니다. | `{action: text, label: 고객번호, value: '00123'}` |
| `fill` | 대상, `value` | `timeout`. `text`와 동일합니다. | `{action: fill, selector: '#customerNo', value: ''}` |
| `select` | 대상, `value` | `timeout`. HTML `select`의 옵션 값을 고릅니다. 목록을 직접 클릭하는 커스텀 콤보는 `click`을 단계별로 사용하세요. | `{action: select, id: status, value: 'ACTIVE'}` |
| `check` | 대상 | `timeout`. 체크박스를 선택합니다. | `{action: check, id: includeClosed}` |
| `uncheck` | 대상 | `timeout`. 체크박스 선택을 해제합니다. | `{action: uncheck, id: includeClosed}` |
| `press` | 대상, `value` | `timeout`. 요소에서 지정한 키를 누릅니다. | `{action: press, id: search, value: Enter}` |
| `wait` | 대상 | `timeout`. 보이는 요소가 나타날 때까지 기다립니다. | `{action: wait, text: 정기점검, timeout: 30000}` |
| `assert_visible` | 대상 | `timeout`. 요소가 보이는지 확인합니다. | `{action: assert_visible, text: 조회 완료}` |
| `assert_text` | 대상, `value` | `timeout`. 요소의 텍스트에 지정 문자열이 포함됐는지 확인합니다. | `{action: assert_text, id: result, value: 조회 완료}` |
| `popup` | 새 창을 여는 클릭 대상 | `timeout`. 클릭으로 열린 팝업을 이후 단계의 대상으로 삼습니다. | `{action: popup, role: button, name: 상세 열기}` |
| `frame` | `selector` 또는 `value` | 현재 탭에서 iframe을 지정합니다. 이후 단계가 해당 프레임을 사용합니다. | `{action: frame, selector: 'iframe#detail'}` |
| `main_frame` | — | 현재 탭의 메인 문서로 돌아갑니다. | `{action: main_frame}` |
| `screenshot` | — | 현재 탭의 전체 화면을 실행 폴더에 PNG로 저장합니다. | `{action: screenshot}` |
| `js` | `script` | `arg`, `timeout`, `label`. 현재 문서에서 자바스크립트를 실행하고 반환값을 표시합니다. | `{action: js, script: '() => document.title'}` |

## 요소 찾기 속성

| 속성 | 값 / 기본값 | 사용 예 |
|---|---|---|
| `selector` | Playwright 선택자 문자열 | `selector: '#queryButton'` |
| `id` | 요소의 HTML ID. 앞에 `#`을 붙이지 않습니다. | `id: queryButton` |
| `attr` | 속성 이름과 문자열 값의 매핑. 모든 속성이 일치해야 합니다. | `attr: {data-testid: query-button}` |
| `syscode` | HTML `syscode` 속성 값 | `syscode: oras` |
| `role` | 접근성 역할 | `role: button` |
| `name` | `role`과 함께 쓰는 접근성 이름. 생략하면 `label`을 사용합니다. | `role: button`, `name: 조회` |
| `label` | 접근성 라벨 우선. 별도 `text`가 없으면 같은 문구로 화면 텍스트도 찾습니다. | `label: 고객번호` |
| `text` | 화면에 보이는 문구 | `text: 조회 완료` |
| `exact` | 기본값 `true`. `false`면 역할 이름·라벨·화면 텍스트를 부분 일치로 찾습니다. | `exact: false` |
| `nth` | 보이는 대상 중 0부터 시작하는 순번. 생략하면 단일 대상을 찾아야 합니다. | `nth: 0` |
| `timeout` | 밀리초. 범위 100~120000. 생략하면 적용된 브라우저 설정의 값(초기 기본값 10000)을 사용합니다. | `timeout: 30000` |

여러 선택자 속성이 있으면 `selector` → `id` → `attr` → `syscode` → `role` 순서로 우선합니다. 이 속성이 모두 없으면 `label`과 `text`로 찾습니다. `wait`에 `timeout: 30000`을 주면 요소가 먼저 나타나는 즉시 다음 단계로 넘어갑니다.

## 자바스크립트 함수 호출

```yaml
step:
  - action: frame
    selector: 'iframe#detail'
  - action: js
    label: 정기점검 메뉴 상태 확인
    script: |
      async ({ menuId }) => {
        return await window.isMenuOpen(menuId)
      }
    arg:
      menuId: regularCheck
    timeout: 10000
  - action: main_frame
```

- `script`는 실행할 함수 또는 표현식입니다. 예시의 `isMenuOpen`은 대상 화면에 공개된 실제 함수명으로 교체하세요. 넥사크로 화면 객체에 속한 함수는 해당 객체 경로를 통해 호출합니다.
- `arg`는 함수에 전달할 값 하나입니다. 여러 인자는 위 예시처럼 객체나 배열로 묶습니다. 문자열, 숫자, 불리언, `null`도 사용할 수 있습니다.
- 함수가 반환한 값은 **JS 반환값** 열과 `result.json`의 `return_value`에 JSON 표기로 표시됩니다. 값이 없으면 `null`로 표시됩니다.
- `false`도 정상 반환값입니다. 검증 실패로 처리하려면 스크립트에서 `throw new Error('정기점검 메뉴가 닫혀 있습니다')`처럼 예외를 발생시키세요. 예외, Promise 거부 또는 실행 대기 시간 초과는 단계 실패로 표시됩니다.
- `frame` 뒤에는 선택한 iframe, `popup` 뒤에는 열린 팝업에서 실행합니다. DOM 요소나 화면 값이 준비될 때까지 기다려야 하면 `js` 앞에 `wait`를 추가하세요.
