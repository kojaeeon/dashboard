import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from app.testing.scenario import BrowserConfig, effective_browser, parse_browser_config, parse_scenario

BROWSER_MD = r'''---
browser: chromium
executable_path: 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
headless: false
viewport: {width: 1920, height: 1080}
timeout: 15000
---
'''


def test_browser_md_and_effective_defaults():
    config = parse_browser_config(BROWSER_MD)
    assert config.browser == 'chromium'
    assert config.executable_path.endswith('msedge.exe')
    assert not config.headless
    scenario = BrowserConfig(base_url='http://example.test', timeout=5000)
    merged = effective_browser(scenario, config)
    assert merged.base_url == 'http://example.test'
    assert merged.timeout == 15000
    assert merged.viewport.model_dump() == {'width': 1920, 'height': 1080}
    assert parse_browser_config('---\nbrowser: {headless: true}\n---').headless
    partial = parse_browser_config('---\nbrowser: chromium\nviewport: {width: 1920}\n---')
    merged = effective_browser(BrowserConfig(viewport={'width': 800, 'height': 600}), partial)
    assert merged.viewport.height == 600


@pytest.mark.parametrize('text', ['---\nbrowser: unknown\n---',
                                '---\nbrowser: chromium\nviewport: {width: 0}\n---',
                                '---\nbrowser: chromium\ntimeout: -1\n---',
                                '---\nheadless: false\n---'])
def test_invalid_browser_md(text):
    with pytest.raises(ValueError):
        parse_browser_config(text)


def test_runner_passes_config_without_forcing_headless(tmp_path, monkeypatch):
    from app.testing.runner import UITestRun
    popen = MagicMock()
    monkeypatch.setattr('app.testing.runner.subprocess.Popen', popen)
    runner = UITestRun(tmp_path / 'runs')
    runner.start('---\nstep: [{action: screenshot}]\n---', 'http://example.test',
                 browser_config=parse_browser_config(BROWSER_MD))
    command = popen.call_args.args[0]
    assert '--headed' not in command and '--headless' not in command
    assert '--browser-config' in command
    config = json.loads((runner.output / 'browser.json').read_text())
    assert config['viewport'] == {'width': 1920, 'height': 1080}
    assert config['base_url'] == 'http://example.test'


@pytest.mark.asyncio
async def test_worker_applies_engine_path_viewport_and_timeout(tmp_path, monkeypatch):
    from app.testing.worker import execute_file
    source = tmp_path / 'scenario.md'
    source.write_text('---\nstep: [{action: screenshot}]\n---')
    executable = tmp_path / 'msedge.exe'
    executable.touch()
    config = parse_browser_config(BROWSER_MD).model_copy(update={'executable_path': str(executable)})
    page = SimpleNamespace(goto=AsyncMock(), screenshot=AsyncMock())
    context = SimpleNamespace(new_page=AsyncMock(return_value=page),
                              tracing=SimpleNamespace(start=AsyncMock(), stop=AsyncMock()),
                              set_default_timeout=MagicMock(), set_default_navigation_timeout=MagicMock())
    browser = SimpleNamespace(new_context=AsyncMock(return_value=context), close=AsyncMock())
    engine = SimpleNamespace(launch=AsyncMock(return_value=browser))
    manager = MagicMock()
    manager.__aenter__ = AsyncMock(return_value=SimpleNamespace(chromium=engine))
    manager.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr('app.testing.worker.async_playwright', lambda: manager)
    report = await execute_file(source, tmp_path / 'out', browser_config=config)
    assert report['status'] == 'passed', report
    engine.launch.assert_awaited_once_with(headless=False, executable_path=str(executable))
    browser.new_context.assert_awaited_once_with(viewport={'width': 1920, 'height': 1080})
    context.set_default_timeout.assert_called_once_with(15000)
    context.set_default_navigation_timeout.assert_called_once_with(15000)


@pytest.mark.asyncio
async def test_ui_browser_selection_drives_execution(user, tmp_path, monkeypatch):
    from nicegui import ui
    from app.common.database import Database
    from app.pages import ui_test
    db = Database(str(tmp_path / 'ui.db'))
    folder = tmp_path / 'md'
    folder.mkdir()
    browser_path = folder / 'edge.md'
    browser_path.write_text(BROWSER_MD)
    db.add_folder(str(folder))
    starts = []
    def start(self, markdown, url, headed, config):
        starts.append((url, headed, config))
        self.output = tmp_path / 'run'
        return 'test-run'
    monkeypatch.setattr(ui_test.UITestRun, 'start', start)

    @ui.page('/browser-md-test')
    def page():
        ui_test.render(db)

    await user.open('/browser-md-test')
    user.find(marker='ui-test-browser-md').click()
    user.find('md / edge.md').click()
    await user.should_see('브라우저 MD 적용 완료 · 실행 시 이 설정을 사용합니다.')
    browser_path.unlink()
    await user.open('/browser-md-test')
    await user.should_see('마지막 브라우저 MD 설정을 복원했습니다.')
    picker = next(iter(user.find(marker='ui-test-browser-md').elements))
    assert picker.value == str(browser_path)
    user.find(kind=ui.button, content='테스트 실행').click()
    await user.should_see('실행 준비 중 · test-run', retries=30)
    assert starts[0][1] is True
    assert starts[0][2].timeout == 15000
    assert starts[0][2].viewport.width == 1920

    picker.set_value(None)
    await user.open('/browser-md-test')
    await user.should_see('시나리오의 browser 설정을 사용합니다.')


async def test_ui_restores_uploaded_browser_override(user, tmp_path):
    from nicegui import ui
    from app.common.database import Database
    from app.pages import ui_test

    db = Database(str(tmp_path / 'ui.db'))

    @ui.page('/uploaded-browser')
    def page():
        ui_test.render(db)

    await user.open('/uploaded-browser')
    upload = next(iter(user.find(kind=ui.upload, content='브라우저 MD 불러오기').elements))
    await upload.handle_uploads([ui.upload.SmallFileUpload('custom.md', 'text/markdown', b'---\nbrowser: chromium\nheadless: true\n---')])
    await user.should_see('브라우저 MD 적용 완료 · 실행 시 이 설정을 사용합니다.')

    await user.open('/uploaded-browser')
    picker = next(iter(user.find(marker='ui-test-browser-md').elements))
    headed = next(iter(user.find(kind=ui.switch, content='브라우저 표시').elements))
    assert picker.options[picker.value] == '업로드 · custom.md'
    assert headed.value is False
    assert json.loads(db.setting(ui_test.BROWSER_SETTING))['config'] == {'browser': 'chromium', 'headless': True}


@pytest.mark.asyncio
async def test_ui_previews_and_runs_sqlite_scenario(user, tmp_path, monkeypatch):
    from nicegui import ui
    from app.common.database import Database
    from app.pages import ui_test

    db = Database(str(tmp_path / 'ui.db'))
    sample = ui_test.SAMPLE_PATH.read_text(encoding='utf-8')
    saved = sample.replace('KJA_BOARD 기본 UI 흐름', '저장된 테스트').replace('timeout: 10000', 'timeout: 15000')
    starts = []

    def start(self, markdown, url, headed, config):
        starts.append(markdown)
        self.output = tmp_path / 'run'
        return 'sqlite-run'

    monkeypatch.setattr(ui_test.UITestRun, 'start', start)

    @ui.page('/sqlite-scenario')
    def page():
        ui_test.render(db)

    await user.open('/sqlite-scenario')
    item_id = db.save_document('정기점검 UI 테스트', sample)
    picker = user.find(kind=ui.select, content='시나리오 선택')
    user.find(marker='ui-test-scenario-refresh').click()
    db.save_document('정기점검 UI 테스트', saved, item_id)
    picker.click()
    user.find('저장 문서 · 정기점검 UI 테스트').click()
    await user.should_see('저장된 테스트')
    preview = next(iter(user.find(kind=ui.code, marker='ui-test-scenario-preview').elements))
    metadata = yaml.safe_load(saved.split('---', 2)[1])
    assert yaml.safe_load(preview.content) == {key: metadata[key] for key in ('browser', 'step')}
    await user.should_not_see(kind=ui.codemirror)
    user.find(kind=ui.button, content='테스트 실행').click()
    await user.should_see('실행 준비 중 · sqlite-run', retries=30)
    assert starts == [saved]
    assert db.list('documents')[0]['content'] == saved
