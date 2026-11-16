import json
from pathlib import Path
import re
from zipfile import ZipFile

import pytest

from app.backup.executor import execute_plan
from app.backup.manifest import Manifest, parse_manifest
from app.backup.planner import build_plan


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
        'node_modules/ignored.js': b'not a backup input',
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


def test_type_backup_preserves_project_paths(release_project):
    manifest, root, base = release_project
    plan = build_plan(manifest, base, scope='categories')
    assert len(plan.files) == 7
    paths = {file.relative for file in plan.files}
    assert 'target/classes/demo/Service$Inner.class' in paths
    assert 'src/main/resources/mapper/Service.xml' in paths
    assert 'web/forms/App.xfdl.js' in paths
    result = execute_plan(plan, output_root=base / 'runs')
    assert result['status'] == 'passed'
    with ZipFile(result['source_zip']) as archive:
        assert set(archive.namelist()) == paths


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


def test_legacy_deploy_config_is_ignored_and_server_untouched(release_project):
    manifest, root, base = release_project
    target = base / 'server/assets/app.js'
    target.parent.mkdir(parents=True)
    target.write_bytes(b'old server file')
    plan = build_plan(manifest, base, scope='files')
    result = execute_plan(plan, output_root=base / 'runs')
    assert result['status'] == 'passed'
    assert target.read_bytes() == b'old server file'
    with ZipFile(result['source_zip']) as archive:
        assert archive.namelist() == ['web/js/app.js']
        assert archive.read('web/js/app.js') == (root / 'web/js/app.js').read_bytes()
    assert json.loads(Path(result['report_path']).read_text())['operation'] == 'backup'
    with pytest.raises(ValueError, match='지원하지 않는 작업'):
        build_plan(manifest, base, 'deploy')
    plan.operation = 'deploy'
    with pytest.raises(ValueError, match='지원하지 않는 작업'):
        execute_plan(plan, output_root=base / 'runs')


def test_changed_source_removes_incomplete_backup(release_project):
    manifest, root, base = release_project
    plan = build_plan(manifest, base, scope='files')
    (root / 'web/js/app.js').write_bytes(b'changed after review')
    result = execute_plan(plan, output_root=base / 'runs')
    assert result['status'] == 'failed'
    assert '원본이 변경' in result['error']
    assert not list(Path(manifest.backup.directory).glob('*.zip'))


def test_archive_name_collision_preserves_existing_archive(release_project, monkeypatch):
    from app.backup import executor
    manifest, root, base = release_project
    plan = build_plan(manifest, base, 'backup')
    plan.backup_dir.mkdir()
    existing = plan.backup_dir / 'fixed.zip'
    existing.write_bytes(b'previous archive must survive')
    monkeypatch.setattr(executor, 'archive_name', lambda _: 'fixed.zip')
    result = execute_plan(plan, output_root=base / 'runs')
    assert result['status'] == 'failed'
    assert existing.read_bytes() == b'previous archive must survive'


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
        build_plan(manifest, base, scope='files')


@pytest.mark.parametrize('source', ['../outside.txt', '/absolute', 'C:\\absolute', 'ok/../../outside'])
def test_mapping_cannot_escape_project(source):
    import yaml
    text = '---\n' + yaml.safe_dump({'title': 'test', 'project': {'root': '.'},
                                    'files': [{'source': source}]}) + '---\n'
    with pytest.raises(ValueError):
        parse_manifest(text)


def test_sample_backup(tmp_path):
    from app.pages.backup import SAMPLE_PATH
    manifest = parse_manifest(SAMPLE_PATH.read_text(encoding='utf-8'))
    manifest.backup.directory = str(tmp_path / 'backups')
    plan = build_plan(manifest, SAMPLE_PATH.parent)
    result = execute_plan(plan, output_root=tmp_path / 'runs')
    assert result['status'] == 'passed', result


def test_invalid_legacy_targets_do_not_affect_backup(release_project):
    import yaml
    manifest, root, base = release_project
    data = manifest.model_dump()
    data['deploy'] = {'method': 'ftp'}  # Old partial deployment config is irrelevant.
    data['files'][0]['target'] = '/old/server/path'
    data['rules'][0]['target'] = 'C:/old/server'
    parsed = parse_manifest('---\n' + yaml.safe_dump(data) + '---\n')
    assert not hasattr(parsed, 'deploy')
    assert build_plan(parsed, base, scope='files').files[0].target == 'web/js/app.js'
