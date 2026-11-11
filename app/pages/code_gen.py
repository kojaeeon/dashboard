"""Code Gen UI. Inject a CodeGenerator to connect the real service."""
from pathlib import PurePosixPath

from nicegui import run, ui

from app.codegen.service import (
    CodeGenerator, GeneratedFile, GenerationRequest, PreviewGenerator, TARGETS, build_zip,
)
from app.common.database import Database
from app.codegen.frontmatter import markdown_sources, read_work_item, work_item_yaml


def render(db: Database, generator: CodeGenerator | None = None):
    provider = generator if generator is not None else PreviewGenerator()
    files: list[GeneratedFile] = []
    selected_path = ''
    archive_name = 'code_gen.zip'
    md_sources = {}

    ui.label('JINJA2 · CODE GENERATOR').classes('eyebrow')
    ui.label('Code Gen').classes('page-title')
    ui.label('테이블과 서비스 정보를 입력하고 생성할 코드를 확인하세요.').classes('text-gray-500')

    def invalidate():
        nonlocal selected_path
        files.clear()
        selected_path = ''
        download_button.disable()
        file_list.refresh()
        preview.refresh()
        status.set_text('입력이 변경되었습니다. 코드 미리보기를 실행하세요.')

    def select_file(path: str):
        nonlocal selected_path
        selected_path = path
        file_list.refresh()
        preview.refresh()

    @ui.refreshable
    def file_list():
        file_count.set_text(f'{len(files)}개 파일')
        if not files:
            ui.label('미리보기 후 생성 파일이 표시됩니다.').classes('text-gray-500')
        for file in files:
            ui.button(PurePosixPath(file.path).name, icon='description',
                      on_click=lambda path=file.path: select_file(path)).props(
                          'flat no-caps align=left' if file.path != selected_path else 'no-caps align=left'
                      ).classes('w-full').mark('code-gen-file')

    @ui.refreshable
    def preview():
        file = next((f for f in files if f.path == selected_path), None)
        if file is None:
            ui.label('코드 미리보기').classes('text-lg font-semibold')
            ui.label('생성 정보를 입력하고 미리보기를 실행하세요.').classes('text-gray-500')
            return
        ui.label(PurePosixPath(file.path).name).classes('text-lg font-semibold break-all')
        ui.label(file.path).classes('text-xs text-gray-500 break-all')
        ui.code(file.content, language=file.language).classes('w-full')

    async def generate():
        nonlocal selected_path, archive_name
        request = GenerationRequest(
            table_name=(table_name.value or '').strip(),
            service_name=(service_name.value or '').strip(),
            service_korean_name=(korean_name.value or '').strip(),
            package_path=(package_path.value or '').strip(),
            targets=tuple(target for target, check in target_checks.items() if check.value),
        )
        generate_button.disable()
        download_button.disable()
        try:
            request.validate()
            # All UI changes stay on the event loop; service work runs off it.
            generated = await run.io_bound(provider.generate, request)
            build_zip(generated)  # Check output paths before enabling download.
            files[:] = generated
            selected_path = files[0].path
            archive_name = f'{request.service_name}.zip'
            status.set_text('샘플 미리보기 · 실제 생성 서비스 연결 전' if isinstance(provider, PreviewGenerator)
                            else '코드 생성 완료')
            download_button.enable()
        except Exception as exc:
            files.clear()
            selected_path = ''
            status.set_text('미리보기를 생성하지 못했습니다.')
            ui.notify(str(exc), type='negative')
        finally:
            file_list.refresh()
            preview.refresh()
            generate_button.enable()

    def download_all():
        try:
            ui.download(build_zip(files), filename=archive_name, media_type='application/zip')
        except ValueError as exc:
            ui.notify(str(exc), type='warning')

    def apply_markdown(event):
        if not event.value:
            md_location.set_text('MD 선택 없음 · 현재 입력값을 유지합니다.')
            md_status.set_text('직접 입력할 수 있습니다.')
            md_yaml.set_content('')
            return
        source = md_sources.get(event.value)
        try:
            if source is None:
                raise ValueError('목록을 새로고침하고 MD를 다시 선택하세요.')
            values = read_work_item(source.read())
        except (OSError, UnicodeError, ValueError) as exc:
            md_status.set_text(f'자동 입력 실패: {exc}')
            md_location.set_text(source.location if source else '')
            md_yaml.set_content('')
            ui.notify(str(exc), type='warning')
            return
        # Parse all four inputs before changing any field.
        table_name.set_value(values['table_name'])
        service_name.set_value(values['service_name'])
        korean_name.set_value(values['service_korean_name'])
        package_path.set_value(values['package_path'])
        invalidate()
        md_location.set_text(source.location)
        md_yaml.set_content(work_item_yaml(values))
        md_status.set_text('생성 정보 4개를 자동 입력했습니다. 입력값은 직접 수정할 수 있습니다.')

    async def reload_markdown():
        refresh_md.disable()
        try:
            sources, warnings = await run.io_bound(markdown_sources, db)
            md_sources.clear()
            md_sources.update({source.key: source for source in sources})
            md_select.set_value(None)
            md_select.set_options({source.key: source.label for source in sources})
            md_status.set_text(f'MD {len(sources)}개 · 선택하면 생성 정보가 자동 입력됩니다.'
                               if sources else 'MD 보기에서 문서를 저장하거나 로컬 폴더를 등록하세요.')
            if warnings:
                ui.notify('일부 폴더를 읽지 못했습니다: ' + '; '.join(warnings), type='warning')
        finally:
            refresh_md.enable()

    with ui.card().classes('w-full'):
        ui.label('MD에서 자동 입력').classes('text-lg font-semibold')
        with ui.row().classes('w-full items-center gap-2'):
            md_select = ui.select({}, label='프론트매터 MD 선택', with_input=True,
                                  clearable=True, on_change=apply_markdown).props('outlined').classes('grow min-w-0').mark('code-gen-md')
            refresh_md = ui.button(icon='refresh', on_click=reload_markdown).props(
                'flat round aria-label="MD 목록 새로고침"').tooltip('MD 목록 새로고침')
        md_location = ui.label('저장 문서 및 등록된 로컬 폴더의 하위 MD 파일').classes('text-xs text-gray-500 break-all')
        md_status = ui.label('MD 목록을 읽는 중입니다.').classes('text-sm text-gray-500')
        with ui.expansion('읽어온 프론트매터 보기', icon='data_object').classes('w-full'):
            md_yaml = ui.code('', language='yaml').classes('w-full')

    with ui.row().classes('w-full items-start gap-5 flex-wrap lg:flex-nowrap'):
        # Disable inputs during service execution so a stale result cannot be downloaded.
        with ui.card().classes('w-full lg:w-2/5 min-w-0'):
            ui.label('생성 정보').classes('text-lg font-semibold')
            table_name = ui.input('테이블명 *', placeholder='KAML.TB_CRA_INSPECTION', on_change=invalidate).props('outlined').classes('w-full')
            ui.label('스키마.테이블 또는 테이블명').classes('text-xs text-gray-500')
            service_name = ui.input('서비스명 *', placeholder='CraInspection', on_change=invalidate).props('outlined').classes('w-full')
            korean_name = ui.input('서비스 한글명 *', placeholder='CRA 정기점검', on_change=invalidate).props('outlined').classes('w-full')
            package_path = ui.input('패키지 경로 *', placeholder='com.kaml.cra.inspection', on_change=invalidate).props('outlined').classes('w-full')
            ui.label('템플릿 세트 · Spring + MyBatis').classes('text-sm')
            ui.label('생성 대상').classes('font-semibold')
            with ui.row().classes('gap-2 flex-wrap'):
                target_checks = {target: ui.checkbox('Mapper XML' if target == 'Mapper' else target,
                                                    value=True, on_change=invalidate) for target in TARGETS}
            generate_button = ui.button('코드 미리보기', icon='code', on_click=generate).classes('w-full').mark('code-gen-preview')
            ui.label('현재는 Jinja2 샘플 템플릿으로 표시합니다.').classes('text-xs text-gray-500')
        with ui.column().classes('w-full lg:w-3/5 min-w-0 gap-5'):
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full items-center justify-between gap-2'):
                    ui.label('생성 파일').classes('text-lg font-semibold')
                    with ui.row().classes('items-center gap-2'):
                        file_count = ui.label('0개 파일').classes('text-sm text-gray-500')
                        download_button = ui.button(icon='download', on_click=download_all).props(
                            'flat round aria-label="전체 다운로드"').tooltip('전체 다운로드 (ZIP)').mark('code-gen-download')
                        download_button.disable()
                file_list()
            with ui.card().classes('w-full min-w-0'):
                preview()
                status = ui.label('미리보기 실행 전').classes('text-sm text-gray-500')

    # Bind after construction: changes at initialization must not reference later controls.
    for control in (table_name, service_name, korean_name, package_path, *target_checks.values()):
        control.bind_enabled_from(generate_button, 'enabled')
    md_select.bind_enabled_from(generate_button, 'enabled')
    refresh_md.bind_enabled_from(generate_button, 'enabled')
    ui.timer(0.1, reload_markdown, once=True)
