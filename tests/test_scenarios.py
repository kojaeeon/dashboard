import json
from pathlib import Path
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from app.testing.scenario import parse_scenario


def test_historical_frontmatter_and_order():
    scenario = parse_scenario('''---
workItem:
  serviceNm: 고객 조회
step:
  - action: menu
    label: CDD
    syscode: oras
  - action: text
    label: 고객번호
    value: "001234"
  - action: click
    attr: {data-testid: search}
---
# 설명은 실행하지 않습니다.
''')
    assert scenario.title == '고객 조회'
    assert [s.action for s in scenario.steps] == ['menu', 'text', 'click']
    assert scenario.steps[1].value == '001234'


@pytest.mark.parametrize('source', [
    '# no frontmatter', '---\nstep: []\n---',
    '---\nstep: [{action: eval, value: "danger"}]\n---',
    '---\nstep: [{action: fill, label: Username}]\n---',
    '---\nstep: [{action: click, unexpected: true}]\n---',
    '---\nbrowser: {base_url: "file:///etc"}\nstep: [{action: screenshot}]\n---',
    '---\nstep: !!python/object:os.system {}\n---',
])
def test_invalid_scenario_rejected_before_browser(source):
    with pytest.raises(ValueError):
        parse_scenario(source)


@pytest.fixture
def fixture_site():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            content = '''<!doctype html><html><body>
            <label>Name <input id="name"></label>
            <button onclick="document.getElementById('result').textContent = document.getElementById('name').value">Apply</button>
            <div id="result">Waiting</div>
            <button onclick="window.open('/popup')">Popup</button>
            <iframe title="child" srcdoc="<p>Inside frame</p>"></iframe>
            </body></html>'''
            if self.path == '/popup':
                content = '<html><body><h1>Popup ready</h1></body></html>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    server.server_close()
    thread.join()


def run_worker(tmp_path, base_url, steps):
    source = tmp_path / 'scenario.md'
    source.write_text('---\nstep:\n' + steps + '\n---\n# Test', encoding='utf-8')
    output = tmp_path / 'run'
    process = subprocess.run(
        [sys.executable, '-m', 'app.testing.worker', '--scenario', str(source),
         '--output', str(output), '--base-url', base_url, '--headless'],
        capture_output=True, text=True, timeout=45)
    assert (output / 'result.json').exists(), process.stderr
    return process, json.loads((output / 'result.json').read_text(encoding='utf-8')), output


def test_real_browser_input_frame_popup_and_evidence(tmp_path, fixture_site):
    process, report, output = run_worker(tmp_path, fixture_site, '''
  - {action: text, label: Name, value: "KJA 테스트"}
  - {action: click, role: button, name: Apply}
  - {action: assert_text, id: result, value: "KJA 테스트"}
  - {action: frame, selector: iframe}
  - {action: assert_visible, text: Inside frame}
  - {action: main_frame}
  - {action: popup, role: button, name: Popup}
  - {action: assert_visible, text: Popup ready}
  - {action: screenshot}
''')
    assert process.returncode == 0, report
    assert report['status'] == 'passed'
    assert all(step['status'] == 'passed' for step in report['steps'])
    assert (output / '009-screenshot.png').stat().st_size > 0
    assert (output / 'trace.zip').stat().st_size > 0


def test_real_failure_stops_flow_and_captures(tmp_path, fixture_site):
    process, report, output = run_worker(tmp_path, fixture_site, '''
  - {action: assert_text, id: result, value: impossible, timeout: 200}
  - {action: click, role: button, name: Apply}
''')
    assert process.returncode == 1
    assert [s['status'] for s in report['steps']] == ['failed', 'skipped']
    assert (output / 'failure.png').stat().st_size > 0
    assert (output / 'trace.zip').stat().st_size > 0


def test_stop_cancels_wait_and_closes_worker(tmp_path, fixture_site):
    from app.testing.runner import UITestRun
    runner = UITestRun(tmp_path / 'runs')
    runner.start('---\nstep:\n  - {action: wait, text: Missing, timeout: 30000}\n---', fixture_site)
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            report = runner.snapshot()
            if report.get('steps') and report['steps'][0]['status'] == 'running':
                break
            time.sleep(.05)
        else:
            pytest.fail(f'Worker did not reach wait: {runner.snapshot()}')
        runner.stop()
        runner.process.wait(timeout=15)
        assert runner.snapshot()['status'] == 'cancelled'
        assert runner.snapshot()['steps'][0]['status'] == 'cancelled'
        assert (runner.output / 'trace.zip').exists()
    finally:
        if runner.running:
            runner.stop()
            runner.process.wait(timeout=15)
