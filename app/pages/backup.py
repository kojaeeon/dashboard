"""ZIP backup menu: frontmatter, file preview, explicit execution."""
from pathlib import Path
from queue import Empty, SimpleQueue

from nicegui import run, ui
from app.common.local_library import markdown_files
from app.backup.executor import execute_plan
from app.backup.manifest import parse_manifest
from app.backup.planner import ROOT, build_plan

SAMPLE_PATH = ROOT / 'examples' / 'backup.md'


def render(db):
    ui.label('BACKUP STUDIO').classes('eyebrow')
    ui.label('백업').classes('page-title')
    ui.label('백업할 파일을 확인하고 ZIP으로 저장하세요.').classes('text-gray-500')
    state = {'plan': None, 'busy': False}
    updates = SimpleQueue()

    def scan_files():
        files = {str(SAMPLE_PATH): '기본 예시 · backup.md'}
        for folder in db.folders():
            try:
                for path in markdown_files(folder['path']):
                    files.setdefault(str(path), f'{path.parent.name} / {path.name}')
            except OSError:
                continue
        return files

    def invalidate():
        state['plan'] = None
        execute_button.disable()
        if not state['busy']:
            message.set_text('계획 만들기를 눌러 백업할 파일을 확인하세요.')

    def update_scope():
        invalidate()
        category_select.set_visibility(scope.value == 'categories')

    def configure():
        try:
            manifest = parse_manifest(source.value or '')
            category_select.set_options([rule.name for rule in manifest.rules])
            category_select.set_value([rule.name for rule in manifest.rules])
            scope.set_value(manifest.backup.scope)
            update_scope()
        except ValueError as exc:
            invalidate()
            message.set_text(str(exc))

    def load_file(path):
        if state['busy']:
            return
        try:
            selected = Path(path)
            if selected.stat().st_size > 2 * 1024 * 1024:
                raise ValueError('설정 문서는 2MB 이하로 작성하세요.')
            source.set_value(selected.read_text(encoding='utf-8-sig'))
            base.set_value(str(selected.parent))
            configure()
        except (OSError, UnicodeError, ValueError) as exc:
            ui.notify(str(exc), type='warning')

    async def upload(e):
        if state['busy']:
            return
        try:
            if e.file.size() > 2 * 1024 * 1024:
                raise ValueError('설정 문서는 2MB 이하로 작성하세요.')
            source.set_value((await e.file.read()).decode('utf-8-sig'))
            base.set_value(str(ROOT))
            configure()
            ui.notify('상대 경로가 있다면 설정 기준 폴더를 확인하세요.')
        except (UnicodeError, ValueError) as exc:
            ui.notify(str(exc), type='warning')

    with ui.row().classes('w-full items-start gap-6 flex-wrap xl:flex-nowrap'):
        with ui.card().classes('w-full xl:w-1/2 min-w-0'):
            ui.label('프론트메터 설정').classes('text-lg font-semibold')
            with ui.row().classes('w-full items-center'):
                file_select = ui.select(scan_files(), value=str(SAMPLE_PATH), label='백업 MD',
                                        on_change=lambda e: load_file(e.value)).classes('grow min-w-0')
                ui.button(icon='refresh', on_click=lambda: file_select.set_options(scan_files())).props(
                    'flat round aria-label="백업 설정 파일 목록 갱신"')
            uploader = ui.upload(label='백업 MD 불러오기', on_upload=upload, auto_upload=True,
                                 max_file_size=2 * 1024 * 1024).props('accept=.md,.markdown').classes('w-full')
            base = ui.input('설정 기준 폴더', value=str(SAMPLE_PATH.parent),
                            on_change=lambda _: invalidate()).classes('w-full')
            source = ui.codemirror(SAMPLE_PATH.read_text(encoding='utf-8'), language='Markdown',
                                   theme='vscodeDark' if db.setting('app_theme', 'light') == 'dark' else 'vscodeLight',
                                   line_wrapping=True, on_change=lambda _: invalidate()).classes('w-full').style('height: 520px')
            apply_button = ui.button('설정 적용', icon='tune', on_click=configure).props('flat')
        with ui.column().classes('w-full xl:w-1/2 min-w-0 gap-4'):
            with ui.card().classes('w-full'):
                scope = ui.select({'all': '프로젝트 전체', 'files': '지정 파일', 'categories': '유형별 전체'},
                                  value='all', label='백업 범위', on_change=lambda _: update_scope()).classes('w-full')
                category_select = ui.select([], multiple=True, label='백업할 유형',
                                            on_change=lambda _: invalidate()).props('use-chips').classes('w-full')
                with ui.row().classes('items-center'):
                    plan_button = ui.button('계획 만들기', icon='fact_check')
                    execute_button = ui.button('ZIP 백업 실행', icon='play_arrow')
                    execute_button.disable()
                    spinner = ui.spinner(size='sm')
                    spinner.set_visibility(False)
                message = ui.label('').classes('text-sm whitespace-pre-wrap break-all')
                summary = ui.label('').classes('text-sm whitespace-pre-wrap break-all')
                warnings = ui.label('').classes('text-sm text-warning whitespace-pre-wrap')
            table = ui.table(columns=[
                {'name': key, 'label': label, 'field': key, 'align': 'left'}
                for key, label in [('category', '유형'), ('source', '프로젝트 상대 경로'),
                                   ('bytes', '바이트'), ('status', '처리'), ('sha256', 'SHA256')]],
                rows=[], row_key='target', pagination=15).classes('w-full')
            downloads = ui.column().classes('w-full')

    def busy(value):
        state['busy'] = value
        for control in (file_select, uploader, base, source, apply_button, scope, category_select, plan_button):
            control.set_enabled(not value)
        execute_button.set_enabled(not value and state['plan'] is not None)
        spinner.set_visibility(value)

    async def make_plan():
        if state['busy']:
            return
        invalidate()
        busy(True)
        table.rows = []
        table.update()
        try:
            manifest = parse_manifest(source.value or '')
            plan = await run.io_bound(build_plan, manifest, base.value,
                                     'backup', scope.value, category_select.value)
            state['plan'] = plan
            rows = [{'category': file.category, 'source': file.relative, 'target': file.relative,
                     'bytes': file.size, 'sha256': file.sha256[:12], 'status': 'ZIP에 포함'}
                    for file in plan.files]
            table.rows = rows
            table.update()
            summary.set_text(f'{plan.manifest.title} · ZIP · {len(plan.files)}개 · {sum(f.size for f in plan.files):,}바이트\n'
                             f'프로젝트: {plan.project}\n백업 폴더: {plan.destination}')
            warnings.set_text('\n'.join(plan.warnings))
            message.set_text('계획 확인 완료 · 위 실행 버튼으로 이 파일들을 처리합니다.')
        except (OSError, ValueError) as exc:
            message.set_text(str(exc))
            summary.set_text('')
        finally:
            busy(False)

    async def execute():
        if state['busy'] or state['plan'] is None:
            return
        plan = state['plan']
        busy(True)
        downloads.clear()
        message.set_text('파일을 ZIP으로 준비하고 있습니다.')
        try:
            result = await run.io_bound(execute_plan, plan, progress=updates.put)
            labels = {'passed': '성공', 'failed': '실패', 'skipped': '건너뜀', 'running': '처리 중'}
            table.rows = [dict(file, sha256=file['sha256'][:12], status=labels.get(file['status'], file['status']))
                          for file in result['files']]
            table.update()
            count = sum(file['status'] == 'passed' for file in result['files'])
            message.set_text(f'{labels[result["status"]]} · {count}/{len(result["files"])}개 완료\n{result["error"]}')
            with downloads:
                ui.label('실행 산출물').classes('text-lg font-semibold')
                for key, label in [('source_zip', '백업 ZIP'), ('report_path', '실행 결과 JSON')]:
                    if result[key]:
                        path = Path(result[key])
                        ui.button(label, icon='download', on_click=lambda p=path: ui.download(str(p))).props('flat no-caps')
                        ui.label(str(path)).classes('text-xs text-gray-500 break-all')
        except (OSError, ValueError) as exc:
            message.set_text(str(exc))
        finally:
            # A second execution always requires a fresh source plan.
            state['plan'] = None
            busy(False)
            while not updates.empty():
                updates.get()

    def show_progress():
        latest = None
        try:
            while True:
                latest = updates.get_nowait()
        except Empty:
            pass
        if latest and state['busy']:
            message.set_text(f'처리 중 · {latest["done"]}/{latest["total"]}개 완료')

    plan_button.on_click(make_plan)
    execute_button.on_click(execute)
    ui.timer(.3, show_progress)
    configure()

