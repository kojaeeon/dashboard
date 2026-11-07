"""Launch, observe and cancel a local UI scenario without blocking the UI."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from app.testing.scenario import parse_scenario, validate_base_url

ROOT = Path(__file__).resolve().parents[2]


class UITestRun:
    def __init__(self, output_root=None):
        self.output_root = Path(output_root or ROOT / 'data' / 'ui_tests')
        self.output = None
        self.process = None

    @property
    def running(self):
        return self.process is not None and self.process.poll() is None

    def start(self, markdown, base_url, headed=False):
        if self.running:
            raise ValueError('이미 실행 중입니다.')
        parse_scenario(markdown)
        validate_base_url(base_url)
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
        self.output = (self.output_root / run_id).resolve()
        self.output.mkdir(parents=True)
        source = self.output / 'scenario.md'
        source.write_text(markdown, encoding='utf-8')
        command = [sys.executable, '-m', 'app.testing.worker', '--scenario', str(source),
                   '--output', str(self.output), '--base-url', base_url,
                   '--headed' if headed else '--headless']
        with (self.output / 'worker.log').open('w', encoding='utf-8') as log:
            self.process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=log,
                                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        return run_id

    def stop(self):
        if self.running:
            (self.output / 'stop').touch()

    def snapshot(self):
        if self.output is None:
            return None
        path = self.output / 'result.json'
        if path.exists():
            report = json.loads(path.read_text(encoding='utf-8'))
        else:
            report = {'status': 'starting', 'steps': [], 'error': ''}
        if not self.running and report['status'] in {'running', 'starting'}:
            report['status'] = 'failed'
            report['error'] = '실행 프로세스가 종료되었습니다. worker.log를 확인하세요.'
        return report
