"""ZIP backup menu: frontmatter, file preview, explicit execution."""
from pathlib import Path
from queue import Empty, SimpleQueue

from nicegui import run, ui
from app.common.database import LAST_BACKUP_DOCUMENT
from app.common.local_library import local_library, markdown_files
from app.backup.executor import execute_plan
from app.backup.manifest import parse_manifest
from app.backup.planner import ROOT, build_plan
from app.backup.sftp import build_copy_plan, execute_copy

SAMPLE_PATH = ROOT / 'examples' / 'backup.md'


def render(db):
    ui.label('BACKUP STUDIO').classes('eyebrow')
    ui.label('백업').classes('page-title')
    ui.label('ZIP 백업 또는 프론트메터의 files 목록을 SFTP로 복사하세요.').classes('text-gray-500')
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

    def refresh_files():
        options = scan_files()
        value = file_select.value
        file_select.set_options(options, value=value if value in options else None)

    def load_file(path, *, remember=True):
        if state['busy'] or not path:
            return
        try:
            selected = Path(path)
            if selected.stat().st_size > 2 * 1024 * 1024:
                raise ValueError('설정 문서는 2MB 이하로 작성하세요.')
            source.set_value(selected.read_text(encoding='utf-8-sig'))
            base.set_value(str(selected.parent))
            document_select.set_value(None)
            configure()
            if remember:
                db.set_setting(LAST_BACKUP_DOCUMENT, f'file:{path}')
        except (OSError, UnicodeError, ValueError) as exc:
            ui.notify(str(exc), type='warning')

    def open_local_file(path):
        if state['busy']:
            return
        selected = str(path)
        options = scan_files()
        options.setdefault(selected, f'{path.parent.name} / {path.name}')
        if file_select.value == selected:
            load_file(selected)
        else:
            file_select.set_options(options, value=selected)

    def saved_documents():
        return {doc['id']: doc['title'] for doc in db.list('documents')}

    def refresh_documents():
        options = saved_documents()
        document_select.set_options(options, value=document_select.value if document_select.value in options else None)

    def load_document(*, remember=True):
        if state['busy'] or document_select.value is None:
            return
        document = db.document(document_select.value)
        if document is None:
            refresh_documents()
            ui.notify('문서가 삭제되었습니다. 다른 문서를 선택하세요.', type='warning')
            return
        content = document['content']
        if len(content.encode('utf-8')) > 2 * 1024 * 1024:
            ui.notify('설정 문서는 2MB 이하로 작성하세요.', type='warning')
            return
        source.set_value(content)
        base.set_value(str(ROOT))
        file_select.set_value(None)
        configure()
        if remember:
            db.set_setting(LAST_BACKUP_DOCUMENT, f"document:{document['id']}")
            ui.notify('저장 문서를 불러왔습니다. 상대 경로가 있다면 설정 기준 폴더를 확인하세요.')

    async def upload(e):
        if state['busy']:
            return
        try:
            if e.file.size() > 2 * 1024 * 1024:
                raise ValueError('설정 문서는 2MB 이하로 작성하세요.')
            source.set_value((await e.file.read()).decode('utf-8-sig'))
            base.set_value(str(ROOT))
            document_select.set_value(None)
            file_select.set_value(None)
            configure()
            ui.notify('상대 경로가 있다면 설정 기준 폴더를 확인하세요.')
        except (UnicodeError, ValueError) as exc:
            ui.notify(str(exc), type='warning')

    document_options = saved_documents()
    file_options = scan_files()
    kind, _, selection = db.setting(LAST_BACKUP_DOCUMENT).partition(':')
    restored_document = None
    if kind == 'document':
        restored_document = next((item_id for item_id in document_options if str(item_id) == selection), None)
    restored_file = selection if kind == 'file' and selection in file_options else None
    initial_file = None if restored_document is not None else restored_file or str(SAMPLE_PATH)

    with ui.row().classes('w-full items-start gap-6 flex-wrap xl:flex-nowrap'):
        with ui.card().classes('w-full xl:w-1/2 min-w-0'):
            ui.label('프론트메터 설정').classes('text-lg font-semibold')
            with ui.row().classes('w-full items-center'):
                document_select = ui.select(document_options, value=restored_document, label='SQLite 저장 문서',
                                            with_input=True).classes('grow min-w-0')
                document_load_button = ui.button('불러오기', icon='description', on_click=load_document)
                document_refresh_button = ui.button(icon='refresh', on_click=refresh_documents).props(
                    'flat round aria-label="저장 문서 목록 갱신"')
            with ui.row().classes('w-full items-center'):
                file_select = ui.select(file_options, value=initial_file, label='백업 MD',
                                        on_change=lambda e: load_file(e.value)).classes('grow min-w-0')
                ui.button(icon='refresh', on_click=refresh_files).props(
                    'flat round aria-label="백업 설정 파일 목록 갱신"')
            uploader = ui.upload(label='백업 MD 불러오기', on_upload=upload, auto_upload=True,
                                 max_file_size=2 * 1024 * 1024).props('accept=.md,.markdown').classes('w-full')
            local_library(db, open_local_file)
            base = ui.input('설정 기준 폴더', value=str(SAMPLE_PATH.parent),
                            on_change=lambda _: invalidate()).classes('w-full')
            source = ui.codemirror(SAMPLE_PATH.read_text(encoding='utf-8'), language='Markdown',
                                   theme='vscodeDark' if db.setting('app_theme', 'light') == 'dark' else 'vscodeLight',
                                   line_wrapping=True, on_change=lambda _: invalidate()).classes('w-full').style('height: 520px')
            apply_button = ui.button('설정 적용', icon='tune', on_click=configure).props('flat')
        with ui.column().classes('w-full xl:w-1/2 min-w-0 gap-4'):
            with ui.card().classes('w-full'):
                scope = ui.select({'all': '프로젝트 전체', 'files': '지정 파일', 'categories': '유형별 전체'},
                                  value='files', label='백업 범위', on_change=lambda _: update_scope()).classes('w-full')
                category_select = ui.select([], multiple=True, label='백업할 유형',
                                            on_change=lambda _: invalidate()).props('use-chips').classes('w-full')
                with ui.row().classes('items-center'):
                    plan_button = ui.button('계획 만들기', icon='fact_check')
                    execute_button = ui.button('ZIP 백업 실행', icon='play_arrow')
                    execute_button.disable()
                    ftp_button = ui.button('FTP COPY', icon='upload_file').props('no-caps')
                    spinner = ui.spinner(size='sm')
                    spinner.set_visibility(False)
                message = ui.label('').classes('text-sm whitespace-pre-wrap break-all')
                summary = ui.label('').classes('text-sm whitespace-pre-wrap break-all')
                warnings = ui.label('').classes('text-sm text-warning whitespace-pre-wrap')
            table = ui.table(columns=[
                {'name': key, 'label': label, 'field': key, 'align': 'left'}
                for key, label in [('category', '유형'), ('source', '프로젝트 경로'),
                                   ('target', '타겟경로')]],
                rows=[], row_key='source', pagination=15).classes('w-full')
            downloads = ui.column().classes('w-full')

    def busy(value):
        state['busy'] = value
        for control in (document_select, document_load_button, document_refresh_button,
                        file_select, uploader, base, source, apply_button, scope, category_select, plan_button, ftp_button):
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
            rows = [{'category': file.category, 'source': file.relative, 'target': file.copy_target,
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

    async def ftp_copy():
        if state['busy']:
            return
        invalidate()
        busy(True)
        downloads.clear()
        table.rows = []
        table.update()
        summary.set_text('')
        warnings.set_text('')
        message.set_text('SFTP 파일 복사를 준비하고 있습니다.')
        try:
            manifest = parse_manifest(source.value or '')
            plan = await run.io_bound(build_copy_plan, manifest, base.value)
            summary.set_text(f'{manifest.title} · SFTP · {len(plan.files)}개\n'
                             f'서버: {manifest.sftp.host}:{manifest.sftp.port}')
            result = await run.io_bound(execute_copy, plan, progress=updates.put)
            labels = {'passed': '성공', 'failed': '실패', 'skipped': '건너뜀'}
            table.rows = [dict(file, sha256=file['sha256'][:12], status=labels.get(file['status'], file['status']))
                          for file in result['files']]
            table.update()
            count = sum(file['status'] == 'passed' for file in result['files'])
            message.set_text(f'FTP COPY {labels[result["status"]]} · {count}/{len(result["files"])}개 완료\n{result["error"]}')
            with downloads:
                ui.button('전송 결과 JSON', icon='download',
                          on_click=lambda: ui.download(result['report_path'])).props('flat no-caps')
        except (OSError, ValueError) as exc:
            message.set_text(str(exc))
        finally:
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
    ftp_button.on_click(ftp_copy)
    ui.timer(.3, show_progress)
    configure()
    if restored_document is not None:
        load_document(remember=False)
    elif restored_file:
        load_file(restored_file, remember=False)


