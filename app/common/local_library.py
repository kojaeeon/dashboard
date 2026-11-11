"""Persistent local folder library with callbacks for opening local files."""
from pathlib import Path
from nicegui import ui


def markdown_files(folder):
    root = Path(folder)
    if not root.is_dir():
        raise FileNotFoundError('폴더가 없거나 접근할 수 없습니다.')
    return sorted((p for p in root.iterdir()
                   if p.is_file() and p.suffix.lower() in {'.md', '.markdown'}),
                  key=lambda p: str(p).casefold())


def local_library(db, on_open):
    ui.separator()
    ui.label('로컬 폴더').classes('text-lg font-semibold')
    path_input = ui.input('폴더 경로', placeholder='C:\\문서\\Markdown').classes('w-full')

    def register():
        try:
            db.add_folder(path_input.value or '')
        except (OSError, ValueError) as exc:
            ui.notify(str(exc), type='warning')
            return
        path_input.set_value('')
        listing.refresh()

    with ui.row().classes('items-center'):
        ui.button('폴더 등록', icon='create_new_folder', on_click=register)
        ui.button(icon='refresh', on_click=lambda: listing.refresh()).props(
            'flat round aria-label="폴더 목록 새로고침"').tooltip('폴더 목록 새로고침')

    @ui.refreshable
    def listing():
        folders = db.folders()
        if not folders:
            ui.label('읽을 폴더 경로를 등록하세요. 등록 폴더 바로 아래의 MD 파일만 조회합니다.').classes('text-xs text-gray-500')
        for item in folders:
            root = Path(item['path'])
            with ui.expansion(root.name or str(root), icon='folder').classes('w-full'):
                ui.label(str(root)).classes('text-xs break-all')
                ui.button('등록 해제', icon='link_off',
                          on_click=lambda folder_id=item['id']: remove(folder_id)).props('flat dense')
                try:
                    files = markdown_files(root)
                except OSError as exc:
                    ui.label(f'폴더를 읽을 수 없습니다: {exc}').classes('text-warning text-xs')
                    continue
                ui.label(f'MD {len(files)}개').classes('text-xs text-gray-500')
                for path in files:
                    ui.button(str(path.relative_to(root)), icon='description',
                              on_click=lambda p=path: on_open(p)).props(
                                  'flat no-caps').classes('w-full justify-start text-left break-all')

    def remove(folder_id):
        db.remove_folder(folder_id)
        listing.refresh()

    listing()
