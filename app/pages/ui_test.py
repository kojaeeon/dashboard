"""UI_TEST menu: inspect a Markdown scenario and run its ordered steps."""
from pathlib import Path

from nicegui import run, ui
from app.common.local_library import markdown_files
from app.testing.runner import ROOT, UITestRun
from app.testing.scenario import parse_scenario

SAMPLE_PATH = ROOT / 'examples' / 'ui-test-smoke.md'


def render(db):
    ui.label('AUTOMATION STUDIO').classes('eyebrow')
    ui.label('UI_TEST').classes('page-title')
    ui.label('프론트메터로 정의하는 UI 테스트').classes('text-gray-500')
    session = UITestRun()
    last_report = None
    stopping = False

    def scan_files():
        files = {str(SAMPLE_PATH): '기본 예시 · ui-test-smoke.md'}
        for folder in db.folders():
            try:
                for path in markdown_files(folder['path']):
                    files.setdefault(str(path), f'{path.parent.name} / {path.name}')
            except OSError:
                continue
        return files

    def validate():
        try:
            scenario = parse_scenario(source.value or '')
            plan.rows = [
                {'number': i, 'action': s.action, 'target': s.label or s.name or s.selector or s.id or s.text or s.url,
                 'status': '대기', 'duration_ms': '', 'strategy': '', 'error': ''}
                for i, s in enumerate(scenario.steps, 1)]
            plan.update()
            scenario_title.set_text(scenario.title)
            message.set_text(f'{len(scenario.steps)}단계 · 프론트메터 검증 완료')
            return scenario
        except (ValueError, TypeError) as exc:
            plan.rows = []
            plan.update()
            message.set_text(str(exc))
            return None

    def load_source(path):
        if session.running:
            return
        try:
            selected = Path(path)
            if selected.stat().st_size > 2 * 1024 * 1024:
                raise ValueError('2MB 이하 파일만 지원합니다.')
            source.set_value(selected.read_text(encoding='utf-8-sig'))
            scenario = validate()
            if scenario:
                base_url.set_value(scenario.browser.base_url)
                headed.set_value(not scenario.browser.headless)
        except (OSError, UnicodeError, ValueError) as exc:
            ui.notify(str(exc), type='warning')

    async def upload(e):
        if session.running:
            return
        try:
            if e.file.size() > 2 * 1024 * 1024:
                raise ValueError('2MB 이하 파일만 지원합니다.')
            source.set_value((await e.file.read()).decode('utf-8-sig'))
            scenario = validate()
            if scenario:
                base_url.set_value(scenario.browser.base_url)
                headed.set_value(not scenario.browser.headless)
        except (UnicodeError, ValueError) as exc:
            ui.notify(str(exc), type='warning')

    with ui.row().classes('w-full items-start gap-6 flex-wrap xl:flex-nowrap'):
        with ui.card().classes('w-full xl:w-1/2 min-w-0'):
            ui.label('시나리오 문서').classes('text-lg font-semibold')
            with ui.row().classes('w-full items-center'):
                file_select = ui.select(scan_files(), value=str(SAMPLE_PATH), label='등록 폴더의 MD',
                                        on_change=lambda e: load_source(e.value)).classes('grow min-w-0')
                ui.button(icon='refresh', on_click=lambda: file_select.set_options(scan_files())).props(
                    'flat round aria-label="시나리오 파일 목록 갱신"')
            uploader = ui.upload(label='시나리오 MD 불러오기', on_upload=upload, auto_upload=True,
                                 max_file_size=2 * 1024 * 1024).props('accept=.md,.markdown').classes('w-full')
            source = ui.codemirror(SAMPLE_PATH.read_text(encoding='utf-8'), language='Markdown',
                                   theme='vscodeDark' if db.setting('app_theme', 'light') == 'dark' else 'vscodeLight',
                                   line_wrapping=True).classes('w-full').style('height: 480px')
            ui.button('단계 확인', icon='checklist', on_click=validate).props('flat')
        with ui.column().classes('w-full xl:w-1/2 min-w-0 gap-4'):
            with ui.card().classes('w-full'):
                scenario_title = ui.label('').classes('text-lg font-semibold')
                base_url = ui.input('시작 URL', value='http://127.0.0.1:8080').classes('w-full')
                headed = ui.switch('브라우저 표시', value=True)
                with ui.row().classes('items-center'):
                    run_button = ui.button('테스트 실행', icon='play_arrow')
                    stop_button = ui.button('중지', icon='stop', color='negative').props('flat')
                    stop_button.disable()
                message = ui.label('시나리오를 확인하고 실행하세요.').classes('text-sm whitespace-pre-wrap break-all')
                output_label = ui.label('').classes('text-xs text-gray-500 break-all')
            plan = ui.table(columns=[
                {'name': key, 'label': label, 'field': key, 'align': 'left'}
                for key, label in [('number', '#'), ('action', '동작'), ('target', '대상'),
                                   ('status', '결과'), ('duration_ms', 'ms'), ('strategy', '요소 찾기'), ('error', '오류')]],
                rows=[], row_key='number', pagination=15).classes('w-full')
            evidence = ui.column().classes('w-full')

    def controls(enabled):
        for element in (run_button, source, file_select, uploader, base_url, headed):
            element.set_enabled(enabled)
        stop_button.set_enabled(not enabled)

    async def start():
        nonlocal last_report, stopping
        if session.running or validate() is None:
            return
        stopping = False
        last_report = None
        evidence.clear()
        controls(False)
        try:
            run_id = await run.io_bound(session.start, source.value, base_url.value, headed.value)
            message.set_text(f'실행 준비 중 · {run_id}')
            output_label.set_text(str(session.output))
            poller.activate()
        except (OSError, ValueError) as exc:
            message.set_text(str(exc))
            controls(True)

    def stop():
        nonlocal stopping
        stopping = True
        session.stop()
        stop_button.disable()
        message.set_text('중지 요청 중 · 브라우저를 정리하고 있습니다.')

    async def poll():
        nonlocal last_report
        try:
            report = await run.io_bound(session.snapshot)
        except (OSError, ValueError):
            return
        if report is None:
            return
        if report != last_report:
            last_report = report
            labels = {'pending': '대기', 'starting': '준비', 'running': '실행 중', 'passed': '성공',
                      'failed': '실패', 'skipped': '건너뜀', 'cancelled': '중지'}
            plan.rows = [dict(step, status=labels.get(step['status'], step['status'])) for step in report['steps']]
            plan.update()
            passed = sum(s['status'] == 'passed' for s in report['steps'])
            status = labels.get(report['status'], report['status'])
            message.set_text(f'{status} · {passed}/{len(report["steps"])} 성공\n{report.get("error", "")}')
        if not session.running:
            poller.deactivate()
            controls(True)
            stop_button.disable()
            evidence.clear()
            with evidence:
                ui.label('실행 결과').classes('text-lg font-semibold')
                with ui.row().classes('gap-2'):
                    for path in sorted(session.output.iterdir()):
                        if path.suffix in {'.json', '.zip', '.png', '.log'}:
                            ui.button(path.name, icon='download',
                                      on_click=lambda p=path: ui.download(str(p))).props('flat dense no-caps')
                screenshot = session.output / 'failure.png'
                if not screenshot.exists():
                    screenshot = session.output / 'final.png'
                if screenshot.exists():
                    ui.image(str(screenshot)).classes('w-full rounded-lg')
        elif stopping:
            message.set_text('중지 요청 중 · 브라우저를 정리하고 있습니다.')

    run_button.on_click(start)
    stop_button.on_click(stop)
    poller = ui.timer(.5, poll, active=False)
    validate()
