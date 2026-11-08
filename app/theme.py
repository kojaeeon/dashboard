"""Shared visual language for the workspace."""
from nicegui import ui


def apply_theme():
    ui.colors(primary='#b89a60', secondary='#7d897b', accent='#cbb788')
    ui.add_css('''
        body { background: #f4f1eb; color: #302c26; }
        body.body--dark { background: #111412; color: #e9e6df; }
        .nicegui-content { padding: 38px 48px 60px; max-width: 1720px;
            margin: auto; gap: 26px; }
        .studio-header { background: #181d19; color: #ede9df;
            padding: 22px 48px; border-bottom: 1px solid #b89a6040;
            box-shadow: none; justify-content: space-between; align-items: center; }
        .brand-symbol { color: #cbb788; font-size: 30px; margin-right: 6px; }
        .brand-name { letter-spacing: .28em; font-size: 23px;
            font-family: Georgia, serif; }
        .brand-caption { font-size: 9px; letter-spacing: .24em; color: #a8afa5; }
        .appearance-controls .q-field { min-width: 138px; }
        .studio-header .q-field__label, .studio-header .q-field__native,
        .studio-header .q-field__marginal { color: #d4ccba; }
        .studio-header .q-field__control:before { border-color: #ffffff30; }
        .studio-navigation { border-bottom: 1px solid #b89a6030; }
        .studio-navigation .q-tabs__content { justify-content: flex-start; gap: 26px; }
        .studio-navigation .q-tab { padding: 12px 6px 20px; min-height: 64px; }
        .q-tab--active { color: #b89a60; }
        .eyebrow { color: #a88b54; font-size: 10px; letter-spacing: .22em;
            margin-top: 18px; }
        .page-title { font-family: Georgia, 'Malgun Gothic', serif;
            font-size: clamp(30px, 3vw, 44px); font-weight: 400;
            letter-spacing: -.035em; line-height: 1.25; }
        .q-tab-panel > .text-gray-500 { margin: 12px 0 32px; }
        .q-card { border: 1px solid #b89a6026; border-radius: 16px;
            padding: 24px; box-shadow: 0 8px 30px #18201506; }
        .body--dark .q-card, .body--dark .q-expansion-item {
            background: #1b201c; }
        .q-btn { border-radius: 8px; box-shadow: none; text-transform: none;
            letter-spacing: .025em; min-height: 38px; }
        .q-btn.bg-primary { color: #171b17 !important; font-weight: 600; }
        .q-field__control { border-radius: 9px; }
        .body--dark .q-field__control:before { border-color: #b89a6038; }
        .search-match-count { display: inline-block; min-width: 72px; margin: 0 12px;
            color: #b89a60; font-variant-numeric: tabular-nums; }
        .cm-editor { position: relative; padding-right: 16px; }
        .search-overview { position: absolute; top: 80px; bottom: 8px; right: 1px;
            width: 13px; background: #b89a6010; z-index: 4; }
        .search-overview[hidden] { display: none; }
        .search-location { position: absolute; left: 1px; width: 11px; height: 4px;
            border: 0; padding: 0; background: #c9a34e; cursor: pointer; }
        .search-location.is-current { background: #f59e0b; height: 6px; }
        .search-location:hover { background: #fcd34d; }
        .cm-editor { border: 1px solid #b89a6038; border-radius: 9px; overflow: hidden; }
        .cm-editor .cm-panels-top { border-bottom: 1px solid #b89a6040; }
        .cm-editor .cm-search { padding: 10px 12px; font-size: 13px; }
        .cm-editor .cm-search input { border-radius: 4px; padding: 4px 6px; }
        .cm-editor .cm-searchMatch { background: #b89a6055; }
        .cm-editor .cm-searchMatch-selected { background: #b89a6099; }
        .q-textarea textarea { line-height: 1.85; }
        .q-expansion-item { border: 1px solid #b89a6028;
            border-radius: 12px; margin-top: 24px; padding: 10px; }
        .nicegui-markdown { line-height: 1.85; }
        .nicegui-markdown pre { overflow-x: auto; border-radius: 8px; }
        .mermaid svg { max-width: 100%; height: auto; }
        .toc-entry { justify-content: flex-start; min-height: 44px; padding: 10px 14px;
            letter-spacing: 0; line-height: 1.5; border-left: 2px solid transparent;
            transition: background-color .15s, border-color .15s; }
        .toc-entry .q-btn__content, .toc-entry .q-btn__content span { color: inherit !important; }
        .toc-entry .q-btn__content { justify-content: flex-start; text-align: left;
            overflow-wrap: anywhere; }
        .toc-entry.toc-level-1 { font-size: 19px; font-weight: 700; color: #76551d !important;
            background: #b89a6012; margin-top: 14px; border-left-color: #aa8647; }
        .toc-entry.toc-level-2 { font-size: 16px; font-weight: 600; color: #315e55 !important;
            margin-top: 7px; }
        .toc-entry.toc-level-3 { font-size: 14px; font-weight: 500; color: #52677f !important; }
        .toc-entry.toc-level-4, .toc-entry.toc-level-5, .toc-entry.toc-level-6 {
            font-size: 13px; font-weight: 400; color: #62675e !important; }
        .body--dark .toc-entry.toc-level-1 { color: #dec28a !important; background: #b89a6015; }
        .body--dark .toc-entry.toc-level-2 { color: #9fcabc !important; }
        .body--dark .toc-entry.toc-level-3 { color: #a8bdd7 !important; }
        .body--dark .toc-entry.toc-level-4, .body--dark .toc-entry.toc-level-5,
        .body--dark .toc-entry.toc-level-6 { color: #b0b7ad !important; }
        .toc-entry:hover { background: #b89a601c; border-left-color: #b89a60; }
        .toc-entry:focus-visible { outline: 2px solid #b89a60; outline-offset: -2px; }
        .document-jump-widget { position: fixed; right: 14px; top: 50%;
            transform: translateY(-50%); z-index: 100; padding: 5px;
            border: 1px solid #b89a6050; border-radius: 28px;
            background: #f4f1ebf5; color: #96763d; box-shadow: 0 6px 24px #00000015; }
        .body--dark .document-jump-widget { background: #1b201cf5; color: #cbb788; }
        .document-jump-widget .q-btn { width: 40px; height: 40px; }
        .document-jump-widget .q-btn:focus-visible { outline: 2px solid #b89a60; outline-offset: 2px; }
        .nicegui-content { padding-right: 82px; }
        .text-gray-500 { color: #8e958c !important; }
        .schedule-calendar { --fc-border-color: #b89a6040;
            --fc-today-bg-color: #b89a601a; --fc-neutral-bg-color: #b89a6012;
            --fc-button-bg-color: #51786b; --fc-button-border-color: #51786b;
            --fc-button-hover-bg-color: #3c5d52; --fc-button-hover-border-color: #3c5d52;
            --fc-button-active-bg-color: #304a41; --fc-button-active-border-color: #304a41; }
        .body--dark .schedule-calendar { --fc-page-bg-color: #1b201c;
            --fc-neutral-text-color: #c7cbbf; --fc-list-event-hover-bg-color: #303a32; }
        .schedule-calendar .fc-event { cursor: pointer; }
        .schedule-calendar .fc-toolbar { gap: 12px; flex-wrap: wrap; }
        .schedule-calendar .fc-toolbar-title { font-size: 1.5rem; }
        @media(max-width: 768px) {
            .nicegui-content { padding: 20px 72px 40px 16px; }
            .studio-header { padding: 18px 20px; gap: 20px; }
            .appearance-controls { width: 100%; }
            .appearance-controls .q-field { flex: 1; min-width: 110px; }
            .q-card { padding: 18px; }
        }
    ''')

