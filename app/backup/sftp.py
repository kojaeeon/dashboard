"""Copy the frontmatter files mappings to an SFTP server."""
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
import errno
import hashlib
from pathlib import Path, PurePosixPath
import stat
from uuid import uuid4

import paramiko

from app.backup.executor import KST
from app.backup.planner import ROOT, PlanFile, checked_child, digest, resolve_from
from app.testing.report_store import write_report


@dataclass
class CopyPlan:
    manifest: object
    base: Path
    project: Path
    files: list[PlanFile]


def build_copy_plan(manifest, base):
    if manifest.sftp is None:
        raise ValueError('프론트메터에 sftp 접속 정보를 작성하세요.')
    if not manifest.files:
        raise ValueError('files에 전송할 source와 target을 작성하세요.')
    project = resolve_from(base, manifest.project.root)
    files = []
    targets = set()
    for mapping in manifest.files:
        source = checked_child(project, mapping.source)
        if not source.is_file():
            raise ValueError(f'전송할 파일이 없습니다: {mapping.source}')
        target = mapping.target
        path = PurePosixPath(target)
        if (not target.strip() or '\\' in target or '..' in path.parts or
                any(ord(c) < 32 for c in target) or str(path) in {'.', '/'} or target.endswith('/')):
            raise ValueError(f'files.target에 원격 파일 경로를 작성하세요: {target}')
        target = str(path)
        if target in targets:
            raise ValueError(f'전송 대상 경로가 중복됩니다: {target}')
        targets.add(target)
        files.append(PlanFile(source, source.relative_to(project).as_posix(), target,
                              'files', source.stat().st_size, digest(source)))
    return CopyPlan(manifest, Path(base), project, files)


def ensure_remote_directory(sftp, directory):
    path = PurePosixPath(directory)
    if str(path) in {'.', '/'}:
        return
    try:
        attributes = sftp.stat(str(path))
    except OSError as exc:
        if exc.errno != errno.ENOENT:
            raise
        ensure_remote_directory(sftp, path.parent)
        sftp.mkdir(str(path))
    else:
        if not stat.S_ISDIR(attributes.st_mode):
            raise ValueError(f'원격 폴더 경로가 파일입니다: {path}')


def execute_copy(plan, *, output_root=None, progress=None):
    config = plan.manifest.sftp
    run_id = datetime.now(KST).strftime('%Y%m%d_%H%M%S') + '-' + uuid4().hex[:8]
    output = Path(output_root or ROOT / 'data' / 'backup_runs') / run_id
    output.mkdir(parents=True, exist_ok=False)
    report = {'id': run_id, 'title': plan.manifest.title, 'operation': 'sftp_copy',
              'status': 'running', 'error': '', 'report_path': str(output / 'result.json'),
              'files': [{'source': f.relative, 'target': f.target, 'category': 'files',
                         'bytes': f.size, 'sha256': f.sha256, 'status': 'pending'} for f in plan.files]}

    def publish():
        write_report(output / 'result.json', report)
        if progress:
            progress({'done': sum(f['status'] == 'passed' for f in report['files']), 'total': len(plan.files)})

    current = None
    publish()
    try:
        with paramiko.SSHClient() as client:
            client.load_system_host_keys()
            if config.known_hosts:
                client.load_host_keys(str(resolve_from(plan.base, config.known_hosts)))
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
            client.connect(hostname=config.host, port=config.port, username=config.username,
                           password=config.password.get_secret_value() if config.password else None,
                           key_filename=str(resolve_from(plan.base, config.private_key)) if config.private_key else None,
                           passphrase=config.passphrase.get_secret_value() if config.passphrase else None,
                           timeout=config.timeout, auth_timeout=config.timeout, banner_timeout=config.timeout,
                           allow_agent=False, look_for_keys=not (config.password or config.private_key))
            with closing(client.open_sftp()) as sftp:
                sftp.get_channel().settimeout(config.timeout)
                for file, current in zip(plan.files, report['files']):
                    current['status'] = 'running'
                    # Verify the opened file before writing anything to the server.
                    if not file.source.resolve().is_relative_to(plan.project):
                        raise ValueError(f'프로젝트 밖으로 변경된 경로입니다: {file.relative}')
                    with file.source.open('rb') as stream:
                        if hashlib.file_digest(stream, 'sha256').hexdigest() != file.sha256:
                            raise ValueError(f'계획 이후 원본이 변경되었습니다: {file.relative}')
                        stream.seek(0)
                        ensure_remote_directory(sftp, PurePosixPath(file.target).parent)
                        sftp.putfo(stream, file.target, file_size=file.size, confirm=True)
                    current['status'] = 'passed'
                    publish()
        report['status'] = 'passed'
    except Exception as exc:
        report['status'] = 'failed'
        error = str(exc)
        for secret in (config.password, config.passphrase):
            if secret and secret.get_secret_value():
                error = error.replace(secret.get_secret_value(), '***')
        report['error'] = error
        if current is not None and current['status'] == 'running':
            current['status'] = 'failed'
    finally:
        for file in report['files']:
            if file['status'] == 'pending':
                file['status'] = 'skipped'
        publish()
    return report
