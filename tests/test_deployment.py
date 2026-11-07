import json
from pathlib import Path
import re
from threading import Thread
from zipfile import ZipFile

import pytest

from app.deployment.executor import execute_plan
from app.deployment.manifest import Manifest, parse_manifest
from app.deployment.planner import build_plan


@pytest.fixture
def release_project(tmp_path):
    root = tmp_path / 'project'
    contents = {
        'README.md': b'# Project',
        'target/classes/demo/Service.class': b'class fixture',
        'target/classes/demo/Service$Inner.class': b'inner class fixture',
        'src/main/resources/mapper/Service.xml': b'<mapper/>',
        'src/main/resources/setup.sql': b'SELECT 1;',
        'web/js/app.js': b'const version = 2;',
        'web/forms/App.xfdl': b'<FDL/>',
        'web/forms/App.xfdl.js': b'// compiled form',
        'node_modules/ignored.js': b'not a deployment input',
    }
    for relative, content in contents.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    manifest = Manifest.model_validate({
        'title': '테스트 릴리스', 'project': {'root': str(root)},
        'backup': {'directory': str(tmp_path / 'backups')},
        'files': [{'source': 'web/js/app.js', 'target': 'assets/app.js'}],
        'rules': [
            {'name': 'java', 'root': 'target/classes', 'include': ['**/*.class'], 'target': 'WEB-INF/classes'},
            {'name': 'sql', 'root': 'src/main/resources', 'include': ['**/*.sql', 'mapper/**/*.xml'], 'target': 'WEB-INF/classes'},
            {'name': 'js', 'root': 'web', 'include': ['**/*.js'], 'exclude': ['**/*.xfdl.js']},
            {'name': 'xfdl', 'root': 'web', 'include': ['**/*.xfdl', '**/*.xfdl.js']},
        ],
        'deploy': {'destination': str(tmp_path / 'server'), 'categories': ['java', 'sql', 'js', 'xfdl']},
    })
    return manifest, root, tmp_path


def test_type_plan_preserves_packages_and_includes_inner_classes(release_project):
    manifest, root, base = release_project
    plan = build_plan(manifest, base, 'deploy')
    assert len(plan.files) == 7
    targets = {file.target for file in plan.files}
    assert 'WEB-INF/classes/demo/Service$Inner.class' in targets
    assert 'WEB-INF/classes/mapper/Service.xml' in targets
    assert 'forms/App.xfdl.js' in targets
    assert len([file for file in plan.files if file.target == 'forms/App.xfdl.js']) == 1


def test_whole_backup_excludes_dependencies_and_its_own_archives(release_project):
    manifest, root, base = release_project
    manifest.backup.directory = str(root / 'archives')
    archive_dir = root / 'archives'
    archive_dir.mkdir()
    (archive_dir / 'old.zip').write_bytes(b'old')
    plan = build_plan(manifest, base, 'backup')
    result = execute_plan(plan, output_root=base / 'runs')
    assert result['status'] == 'passed'
    assert re.match(r'테스트_릴리스_\d{8}_\d{6}_\d{6}\.zip', Path(result['source_zip']).name)
    with ZipFile(result['source_zip']) as archive:
        assert 'README.md' in archive.namelist()
        assert not any('node_modules' in name or name.startswith('archives/') for name in archive.namelist())
    second_plan = build_plan(manifest, base, 'backup')
    assert len(second_plan.files) == len(plan.files)


def test_explicit_file_mapping_copy_has_no_server_backup(release_project):
    manifest, root, base = release_project
    target = Path(manifest.deploy.destination) / 'assets/app.js'
    target.parent.mkdir(parents=True)
    target.write_bytes(b'old app')
    plan = build_plan(manifest, base, 'deploy', scope='files')
    result = execute_plan(plan, output_root=base / 'runs')
    assert result['status'] == 'passed', result
    assert target.read_bytes() == (root / 'web/js/app.js').read_bytes()
    assert 'previous_zip' not in result
    assert not list(Path(manifest.backup.directory).glob('*배포전*'))
    with ZipFile(result['source_zip']) as archive:
        assert archive.read('web/js/app.js') == target.read_bytes()
    assert json.loads(Path(result['report_path']).read_text(encoding='utf-8'))['status'] == 'passed'


def test_changed_source_aborts_before_deployment(release_project):
    manifest, root, base = release_project
    plan = build_plan(manifest, base, 'deploy', scope='files')
    (root / 'web/js/app.js').write_bytes(b'changed after review')
    result = execute_plan(plan, output_root=base / 'runs')
    assert result['status'] == 'failed'
    assert '원본이 변경' in result['error']
    assert not Path(manifest.deploy.destination).exists()
    assert not list(Path(manifest.backup.directory).glob('*.zip'))


def test_archive_name_collision_preserves_existing_archive(release_project, monkeypatch):
    from app.deployment import executor
    manifest, root, base = release_project
    plan = build_plan(manifest, base, 'backup')
    plan.backup_dir.mkdir()
    existing = plan.backup_dir / 'fixed.zip'
    existing.write_bytes(b'previous archive must survive')
    monkeypatch.setattr(executor, 'archive_name', lambda _: 'fixed.zip')
    result = execute_plan(plan, output_root=base / 'runs')
    assert result['status'] == 'failed'
    assert existing.read_bytes() == b'previous archive must survive'


def test_changed_destination_aborts_before_overwrite(release_project):
    manifest, root, base = release_project
    target = Path(manifest.deploy.destination) / 'assets/app.js'
    target.parent.mkdir(parents=True)
    target.write_bytes(b'reviewed destination')
    plan = build_plan(manifest, base, 'deploy', scope='files')
    target.write_bytes(b'external update')
    result = execute_plan(plan, output_root=base / 'runs')
    assert result['status'] == 'failed'
    assert '대상이 변경' in result['error']
    assert target.read_bytes() == b'external update'


def test_conflicting_targets_are_rejected(release_project):
    manifest, root, base = release_project
    manifest.files.append(type(manifest.files[0])(source='README.md', target='assets/app.js'))
    with pytest.raises(ValueError, match='중복'):
        build_plan(manifest, base, 'deploy', scope='files')


def test_project_symlink_cannot_include_external_files(release_project):
    manifest, root, base = release_project
    outside = base / 'outside'
    outside.mkdir()
    (outside / 'secret.txt').write_text('outside', encoding='utf-8')
    link = root / 'linked'
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip('Creating symlinks is not permitted on this host')
    plan = build_plan(manifest, base, 'backup')
    assert not any('secret' in file.relative for file in plan.files)
    manifest.files[0].source = 'linked/secret.txt'
    with pytest.raises(ValueError, match='밖으로'):
        build_plan(manifest, base, 'deploy', scope='files')


@pytest.mark.parametrize('source', ['../outside.txt', '/absolute', 'C:\\absolute', 'ok/../../outside'])
def test_mapping_cannot_escape_project(source):
    import yaml
    text = '---\n' + yaml.safe_dump({'title': 'test', 'project': {'root': '.'},
                                    'files': [{'source': source}]}) + '---\n'
    with pytest.raises(ValueError):
        parse_manifest(text)


def test_partial_transfer_preserves_source_archive(release_project, monkeypatch):
    from app.deployment import executor
    from app.deployment.transports import CopyTransport
    manifest, root, base = release_project
    plan = build_plan(manifest, base, 'deploy', categories=['sql'])

    class FailingTransport(CopyTransport):
        calls = 0

        def write_from(self, relative, stream):
            self.calls += 1
            if self.calls == 2:
                raise OSError('simulated transfer failure')
            super().write_from(relative, stream)

    monkeypatch.setattr(executor, 'CopyTransport', FailingTransport)
    result = execute_plan(plan, output_root=base / 'runs')
    assert result['status'] == 'failed'
    assert [file['status'] for file in result['files']] == ['passed', 'failed']
    assert Path(result['source_zip']).exists()


@pytest.fixture
def ftp_server(tmp_path, monkeypatch):
    from pyftpdlib.authorizers import DummyAuthorizer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers import FTPServer
    root = tmp_path / 'ftp'
    root.mkdir()
    authorizer = DummyAuthorizer()
    # This account cannot RETR/download any server files.
    authorizer.add_user('deploy', 'fixture-password', str(root), perm='eladfmwMT')

    class Handler(FTPHandler):
        pass

    Handler.authorizer = authorizer
    server = FTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, kwargs={'timeout': .05, 'handle_exit': False}, daemon=True)
    thread.start()
    monkeypatch.setenv('FIXTURE_FTP_PASSWORD', 'fixture-password')
    yield root, server.socket.getsockname()[1]
    server.close_all()
    thread.join(timeout=3)


def test_real_ftp_transfer_without_server_read_permission(release_project, ftp_server):
    manifest, project, base = release_project
    remote_root, port = ftp_server
    manifest.deploy.method = 'ftp'
    manifest.deploy.destination = '/apps/demo'
    from app.deployment.manifest import FTPSettings
    manifest.deploy.ftp = FTPSettings(host='127.0.0.1', port=port, username='deploy', password_env='FIXTURE_FTP_PASSWORD')
    previous = remote_root / 'apps/demo/WEB-INF/classes/mapper/Service.xml'
    previous.parent.mkdir(parents=True)
    previous.write_bytes(b'old remote mapper')
    plan = build_plan(manifest, base, 'deploy')
    result = execute_plan(plan, output_root=base / 'runs')
    assert result['status'] == 'passed', result
    for file in plan.files:
        assert (remote_root / 'apps/demo' / file.target).read_bytes() == file.source.read_bytes()
    assert 'previous_zip' not in result
    assert not list(Path(manifest.backup.directory).glob('*배포전*'))
    assert not list(remote_root.rglob('.kja-*'))


def test_target_root_alias_and_legacy_backup_is_ignored(release_project):
    import yaml
    manifest, root, base = release_project
    data = manifest.model_dump()
    data['deploy']['target_root'] = data['deploy'].pop('destination')
    data['deploy']['backup_before_deploy'] = True
    parsed = parse_manifest('---\n' + yaml.safe_dump(data) + '---\n')
    plan = build_plan(parsed, base, 'deploy', scope='files')
    assert plan.destination == str(base / 'server')
    assert plan.files[0].target == 'assets/app.js'
    assert not hasattr(parsed.deploy, 'backup_before_deploy')


def test_class_category_and_changed_target_root(tmp_path):
    from app.pages.deploy_backup import SAMPLE_PATH, resolved_target
    parsed = parse_manifest(SAMPLE_PATH.read_text(encoding='utf-8'))
    assert {rule.name for rule in parsed.rules} >= {'java', 'class'}
    parsed.backup.directory = str(tmp_path / 'backups')
    parsed.deploy.destination = str(tmp_path / 'custom-target')
    plan = build_plan(parsed, SAMPLE_PATH.parent, 'deploy', categories=['class'])
    assert [file.relative for file in plan.files] == ['target/classes/demo/Hello.class']
    assert plan.files[0].target == 'WEB-INF/classes/demo/Hello.class'
    assert Path(resolved_target(plan, plan.files[0].target)) == tmp_path / 'custom-target/WEB-INF/classes/demo/Hello.class'
    result = execute_plan(plan, output_root=tmp_path / 'runs')
    assert result['status'] == 'passed', result
    assert (tmp_path / 'custom-target/WEB-INF/classes/demo/Hello.class').read_bytes() == plan.files[0].source.read_bytes()
