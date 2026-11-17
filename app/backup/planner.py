"""Resolve and fingerprint the exact files shown for review."""
from dataclasses import dataclass
import fnmatch
from functools import lru_cache
import hashlib
import os
from pathlib import Path

from app.backup.manifest import Manifest, relative_path

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def resolve_from(base, value):
    return (Path(base) / Path(value).expanduser()).resolve()


def matches(path, patterns):
    for pattern in patterns:
        parts = path.split('/')
        pattern_parts = pattern.replace('\\', '/').removeprefix('./').split('/')

        @lru_cache(maxsize=None)
        def match(i, j):
            if j == len(pattern_parts):
                return i == len(parts)
            if pattern_parts[j] == '**':
                return match(i, j + 1) or (i < len(parts) and match(i + 1, j))
            return i < len(parts) and fnmatch.fnmatchcase(parts[i], pattern_parts[j]) and match(i + 1, j + 1)

        if match(0, 0):
            return True
    return False


def checked_child(root, relative):
    path = (root / relative_path(relative, allow_dot=True)).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'기준 폴더 밖으로 연결된 경로입니다: {relative}')
    return path


@dataclass(frozen=True)
class PlanFile:
    source: Path
    relative: str
    target: str
    category: str
    size: int
    sha256: str
    copy_target: str = ''


@dataclass
class Plan:
    manifest: Manifest
    operation: str
    scope: str
    project: Path
    backup_dir: Path
    destination: str
    files: list[PlanFile]
    warnings: list[str]


def build_plan(manifest, base, operation='backup', scope=None, categories=None):
    if operation != 'backup':
        raise ValueError('지원하지 않는 작업입니다.')
    project = resolve_from(base, manifest.project.root)
    if not project.is_dir():
        raise ValueError(f'프로젝트 폴더가 없습니다: {project}')
    backup_dir = resolve_from(base, manifest.backup.directory)
    if project.is_relative_to(backup_dir):
        raise ValueError('백업 폴더는 프로젝트 루트 또는 그 상위 폴더와 다르게 지정하세요.')
    scope = scope or manifest.backup.scope
    if scope not in {'all', 'files', 'categories'}:
        raise ValueError('전체 / 파일별 / 유형별 범위를 선택하세요.')
    destination = str(backup_dir)
    excluded_roots = [backup_dir, (ROOT / 'data' / 'backup_runs').resolve(),
                      (ROOT / 'data' / 'deployments').resolve()]

    def allowed(path):
        if not path.is_relative_to(project):
            return False
        relative = path.relative_to(project).as_posix()
        return not matches(relative, manifest.project.exclude) and not any(path.is_relative_to(p) for p in excluded_roots)

    def walk(root):
        for directory, dirs, names in os.walk(root, followlinks=False):
            parent = Path(directory)
            dirs[:] = sorted(name for name in dirs if
                              not (parent / name).is_symlink() and
                              not getattr(parent / name, 'is_junction', lambda: False)() and
                              allowed((parent / name).resolve()) and
                              not matches((parent / name).relative_to(project).as_posix() + '/', manifest.project.exclude))
            for name in sorted(names):
                path = parent / name
                if not path.is_symlink() and path.is_file() and allowed(path.resolve()):
                    yield path.resolve()

    selected = []
    warnings = []
    if scope == 'all':
        selected = [(path, path.relative_to(project).as_posix(), 'all') for path in walk(project)]
    elif scope == 'files':
        if not manifest.files:
            raise ValueError('files에 백업할 source 경로를 작성하세요.')
        for mapping in manifest.files:
            path = checked_child(project, mapping.source)
            if not path.is_file() or not allowed(path):
                raise ValueError(f'파일이 없거나 제외된 경로입니다: {mapping.source}')
            selected.append((path, path.relative_to(project).as_posix(), 'files'))
    else:
        chosen = categories if categories is not None else [r.name for r in manifest.rules]
        if not chosen:
            raise ValueError('백업할 유형을 선택하세요.')
        unknown = set(chosen) - {rule.name for rule in manifest.rules}
        if unknown:
            raise ValueError(f'정의되지 않은 유형: {", ".join(sorted(unknown))}')
        for rule in manifest.rules:
            if rule.name not in chosen:
                continue
            root = checked_child(project, rule.root)
            count = 0
            if root.is_dir():
                for path in walk(root):
                    relative = path.relative_to(root).as_posix()
                    if matches(relative, rule.include) and not matches(relative, rule.exclude):
                        selected.append((path, path.relative_to(project).as_posix(), rule.name))
                        count += 1
            if not count:
                warnings.append(f'{rule.name}: 일치하는 파일 없음 ({rule.root})')

    files = []
    targets = {}
    # ZIP entry paths and optional SFTP destinations are independent.
    copy_targets = {relative_path(mapping.source): mapping.target
                    for mapping in manifest.files if mapping.target.strip()}
    for source, target, category in selected:
        target = relative_path(target)
        key = target.casefold()  # Avoid ambiguous paths when restoring on case-insensitive systems.
        if key in targets:
            if targets[key] == source:
                continue
            raise ValueError(f'서로 다른 파일의 대상 경로가 중복됩니다: {target}')
        targets[key] = source
        files.append(PlanFile(source, source.relative_to(project).as_posix(), target,
                              category, source.stat().st_size, digest(source),
                              copy_targets.get(source.relative_to(project).as_posix(), '')))
    if not files:
        raise ValueError('선택 범위에 파일이 없습니다. 경로·유형·빌드 결과를 확인하세요.')
    return Plan(manifest, operation, scope, project, backup_dir, destination, files, warnings)

