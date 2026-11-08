import os
from dotenv import load_dotenv
from nicegui import ui
from app.common.database import Database
from app.common.markdown_viewer import MermaidRenderer
from app.menu import build_menu
from app.theme import apply_theme
from app.pages import markdown, work, ui_test, deploy_backup, schedule

load_dotenv()
db = Database(os.getenv('DASHBOARD_DB_PATH', 'data/dashboard.db'))


@ui.page('/')
def index():
    apply_theme()
    handlers = {}
    theme = db.setting('mermaid_theme', 'default')
    tabs, md_tab, work_tab, test_tab, deploy_tab, schedule_tab = build_menu(
        app_theme=db.setting('app_theme', 'light'),
        mermaid_theme=theme if theme in MermaidRenderer.THEMES else 'default',
        mermaid_themes=MermaidRenderer.THEMES,
        on_app_theme=lambda e: handlers['app_theme'](e) if handlers else None,
        on_mermaid_theme=lambda e: handlers['mermaid_theme'](e) if handlers else None,
    )
    with ui.tab_panels(tabs, value=md_tab).classes('w-full bg-transparent'):
        with ui.tab_panel(md_tab).classes('p-0'):
            handlers.update(markdown.render(db))
        with ui.tab_panel(work_tab).classes('p-0'):
            work.render(db)
        with ui.tab_panel(schedule_tab).classes('p-0'):
            schedule.render(db)
        with ui.tab_panel(test_tab).classes('p-0'):
            ui_test.render(db)
        with ui.tab_panel(deploy_tab).classes('p-0'):
            deploy_backup.render(db)


def run():
    ui.run(title='KJA_BOARD', host=os.getenv('DASHBOARD_HOST', '127.0.0.1'),
           port=int(os.getenv('DASHBOARD_PORT', '8080')), reload=False)


if __name__ == '__main__':
    run()

