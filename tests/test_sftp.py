import errno
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import yaml

from app.backup.manifest import parse_manifest
from app.backup import sftp


@pytest.fixture
def copy_setup(tmp_path, monkeypatch):
    project = tmp_path / 'project'
    project.mkdir()
    (project / 'hello.txt').write_bytes(b'hello')
    (project / 'second.txt').write_bytes(b'second')
    data = {'title': 'copy', 'project': {'root': 'project'},
            'sftp': {'host': 'server.example', 'username': 'deploy', 'password': 'secret-password'},
            'files': [{'source': 'hello.txt', 'target': '/srv/app/hello.txt'},
                      {'source': 'second.txt', 'target': '/srv/app/second.txt'}]}
    manifest = parse_manifest('---\n' + yaml.safe_dump(data) + '---\n')
    client = MagicMock()
    client.__enter__.return_value = client
    remote = client.open_sftp.return_value
    remote.stat.side_effect = FileNotFoundError(errno.ENOENT, 'missing')
    uploaded = {}

    def put(stream, target, **kwargs):
        uploaded[target] = stream.read()

    remote.putfo.side_effect = put
    factory = MagicMock(return_value=client)
    monkeypatch.setattr(sftp.paramiko, 'SSHClient', factory)
    return SimpleNamespace(base=tmp_path, project=project, manifest=manifest,
                           client=client, remote=remote, factory=factory, uploaded=uploaded)


def test_copy_mappings_authentication_directories_and_report(copy_setup):
    env = copy_setup
    env.manifest.sftp.known_hosts = 'known_hosts'
    plan = sftp.build_copy_plan(env.manifest, env.base)
    result = sftp.execute_copy(plan, output_root=env.base / 'runs')
    assert result['status'] == 'passed'
    assert env.uploaded == {'/srv/app/hello.txt': b'hello', '/srv/app/second.txt': b'second'}
    assert env.remote.mkdir.call_args_list[0].args == ('/srv',)
    assert env.remote.mkdir.call_args_list[1].args == ('/srv/app',)
    assert env.client.connect.call_args.kwargs['password'] == 'secret-password'
    env.client.load_host_keys.assert_called_once_with(str(env.base / 'known_hosts'))
    assert isinstance(env.client.set_missing_host_key_policy.call_args.args[0], sftp.paramiko.RejectPolicy)
    env.remote.close.assert_called_once()
    assert 'secret-password' not in json.dumps(result)
    assert json.loads(Path(result['report_path']).read_text(encoding='utf-8')) == result


def test_transfer_failure_stops_and_redacts_credentials(copy_setup):
    env = copy_setup
    env.remote.putfo.side_effect = OSError('failed secret-password')
    result = sftp.execute_copy(sftp.build_copy_plan(env.manifest, env.base), output_root=env.base / 'runs')
    assert result['status'] == 'failed'
    assert [f['status'] for f in result['files']] == ['failed', 'skipped']
    assert result['error'] == 'failed ***'
    assert env.remote.putfo.call_count == 1
    env.remote.close.assert_called_once()


def test_changed_source_is_not_uploaded(copy_setup):
    env = copy_setup
    plan = sftp.build_copy_plan(env.manifest, env.base)
    (env.project / 'hello.txt').write_bytes(b'changed')
    result = sftp.execute_copy(plan, output_root=env.base / 'runs')
    assert result['status'] == 'failed'
    assert '원본이 변경' in result['error']
    env.remote.putfo.assert_not_called()


@pytest.mark.parametrize('target', ['', '../outside', '/srv/../file', '/srv/', 'a\\b'])
def test_invalid_targets_fail_before_connection(copy_setup, target):
    env = copy_setup
    env.manifest.files[0].target = target
    with pytest.raises(ValueError, match='target'):
        sftp.build_copy_plan(env.manifest, env.base)
    env.factory.assert_not_called()


def test_duplicate_targets_fail_before_connection(copy_setup):
    env = copy_setup
    env.manifest.files[1].target = env.manifest.files[0].target
    with pytest.raises(ValueError, match='중복'):
        sftp.build_copy_plan(env.manifest, env.base)
    env.factory.assert_not_called()


def test_connection_failure_skips_all_files(copy_setup):
    env = copy_setup
    env.client.connect.side_effect = sftp.paramiko.AuthenticationException('Authentication failed')
    result = sftp.execute_copy(sftp.build_copy_plan(env.manifest, env.base), output_root=env.base / 'runs')
    assert result['status'] == 'failed'
    assert all(f['status'] == 'skipped' for f in result['files'])
    env.client.open_sftp.assert_not_called()
    env.client.__exit__.assert_called_once()


def test_missing_connection_config_is_actionable(copy_setup):
    env = copy_setup
    env.manifest.sftp = None
    with pytest.raises(ValueError, match='sftp 접속 정보'):
        sftp.build_copy_plan(env.manifest, env.base)
    env.factory.assert_not_called()


@pytest.mark.asyncio
async def test_ftp_button_executes_frontmatter_files(user, copy_setup, monkeypatch):
    from nicegui import ui
    from app.common.database import Database
    from app.pages import backup

    env = copy_setup
    sample = env.base / 'copy.md'
    data = env.manifest.model_dump(exclude={'sftp'})
    data['sftp'] = {'host': 'server.example', 'username': 'deploy', 'password': 'secret-password'}
    sample.write_text('---\n' + yaml.safe_dump(data) + '---\n', encoding='utf-8')
    monkeypatch.setattr(backup, 'SAMPLE_PATH', sample)
    monkeypatch.setattr(sftp, 'ROOT', env.base)

    @ui.page('/sftp-copy')
    def page():
        backup.render(Database(str(env.base / 'ui.db')))

    await user.open('/sftp-copy')
    user.find(kind=ui.button, content='FTP COPY').click()
    await user.should_see('FTP COPY 성공 · 2/2개 완료', retries=30)
    await user.should_see('전송 결과 JSON')
    assert env.uploaded['/srv/app/hello.txt'] == b'hello'
    assert len(env.uploaded) == 2
