"""Stage an immutable local ZIP, then transfer files relative to the target root."""
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import re
from uuid import uuid4
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from app.deployment.planner import ROOT, checked_child, digest
from app.deployment.transports import CopyTransport, FTPTransport
from app.testing.report_store import write_report

KST = timezone(timedelta(hours=9))


def archive_name(title):
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f\s]+', '_', title).strip('._')[:100] or 'backup'
    return f'{title}_{datetime.now(KST):%Y%m%d_%H%M%S_%f}.zip'


def package_sources(plan):
    plan.backup_dir.mkdir(parents=True, exist_ok=True)
    destination = plan.backup_dir / archive_name(plan.manifest.title)
    created = False
    try:
        with ZipFile(destination, 'x', compression=ZIP_DEFLATED, allowZip64=True) as archive:
            created = True
            unique = {file.relative: file for file in plan.files}
            for relative, file in unique.items():
                if not file.source.resolve().is_relative_to(plan.project):
                    raise ValueError(f'프로젝트 밖으로 변경된 경로입니다: {relative}')
                hasher = hashlib.sha256()
                info = ZipInfo.from_file(file.source, arcname=relative, strict_timestamps=False)
                info.compress_type = ZIP_DEFLATED
                with file.source.open('rb') as source, archive.open(info, 'w', force_zip64=True) as output:
                    while chunk := source.read(1024 * 1024):
                        output.write(chunk)
                        hasher.update(chunk)
                if hasher.hexdigest() != file.sha256:
                    raise ValueError(f'계획 이후 원본이 변경되었습니다. 계획을 다시 만드세요: {relative}')
        return destination
    except BaseException:
        if created:
            destination.unlink(missing_ok=True)
        raise


def execute_plan(plan, *, output_root=None, progress=None):
    run_id = datetime.now(KST).strftime('%Y%m%d_%H%M%S') + '-' + uuid4().hex[:8]
    output = Path(output_root or ROOT / 'data' / 'deployments') / run_id
    output.mkdir(parents=True, exist_ok=False)
    report = {'id': run_id, 'title': plan.manifest.title, 'operation': plan.operation,
              'scope': plan.scope, 'destination': plan.destination, 'status': 'running',
              'error': '', 'source_zip': '', 'report_path': str(output / 'result.json'),
              'files': [{'source': f.relative, 'target': f.relative if plan.operation == 'backup' else f.target, 'category': f.category,
                         'bytes': f.size, 'sha256': f.sha256, 'status': 'pending'} for f in plan.files]}

    def publish():
        write_report(output / 'result.json', report)
        if progress:
            progress({'status': report['status'], 'done': sum(f['status'] == 'passed' for f in report['files']),
                      'total': len(plan.files)})

    publish()
    try:
        source_zip = package_sources(plan)
        report['source_zip'] = str(source_zip)
        if plan.operation == 'backup':
            for file in report['files']:
                file['status'] = 'passed'
            report['status'] = 'passed'
            return report
        config = plan.manifest.deploy
        transport = CopyTransport(Path(plan.destination)) if config.method == 'copy' else FTPTransport(config.ftp, plan.destination)
        with transport:
            existing = {file.target: transport.exists(file.target) for file in plan.files}
            for file in plan.files:
                if existing[file.target] and not config.overwrite:
                    raise ValueError(f'덮어쓰기가 꺼져 있습니다: {file.target}')
                if config.method == 'copy':
                    path = checked_child(Path(plan.destination), file.target)
                    current = digest(path) if existing[file.target] else None
                    if current != file.previous_sha256:
                        raise ValueError(f'계획 이후 대상이 변경되었습니다. 계획을 다시 만드세요: {file.target}')
            with ZipFile(source_zip) as archive:
                for file, result in zip(plan.files, report['files']):
                    result['status'] = 'running'
                    publish()
                    try:
                        with archive.open(file.relative) as source:
                            transport.write_from(file.target, source)
                        result['status'] = 'passed'
                    except Exception as exc:
                        result['status'] = 'failed'
                        result['error'] = str(exc)
                        raise
                    publish()
        report['status'] = 'passed'
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = str(exc)
    finally:
        for file in report['files']:
            if file['status'] == 'pending':
                file['status'] = 'skipped'
        publish()
    return report
