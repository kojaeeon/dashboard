"""Application navigation and appearance controls."""
from nicegui import ui


def build_menu(*, app_theme, mermaid_theme, mermaid_themes,
               on_app_theme, on_mermaid_theme):
    with ui.header().classes('studio-header'):
        with ui.row().classes('items-center gap-3'):
            ui.icon('auto_awesome').classes('brand-symbol')
            with ui.column().classes('gap-0'):
                ui.label('KJA_BOARD').classes('brand-name')
                ui.label('PERSONAL WORKSPACE').classes('brand-caption')
        with ui.row().classes('appearance-controls items-center gap-4'):
            ui.select({'light': '라이트', 'dark': '다크'}, value=app_theme,
                      label='화면 테마', on_change=on_app_theme).props('dense outlined')
            ui.select(list(mermaid_themes), value=mermaid_theme,
                      label='Mermaid 테마', on_change=on_mermaid_theme).props('dense outlined')
    with ui.tabs().classes('studio-navigation w-full justify-start') as tabs:
        md_tab = ui.tab('MD 보기', icon='description')
        work_tab = ui.tab('Work', icon='task_alt')
        schedule_tab = ui.tab('일정', icon='calendar_month')
        test_tab = ui.tab('UI_TEST', icon='science')
        deploy_tab = ui.tab('배포/백업', icon='drive_file_move')
    return tabs, md_tab, work_tab, test_tab, deploy_tab, schedule_tab

