"""Frontmatter configuration shared by backup and deployment."""
from pathlib import PurePosixPath
import re
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator
import yaml


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Project(StrictModel):
    root: str
    exclude: list[str] = Field(default_factory=lambda: [
        '.git/**', '**/.git/**', '.venv/**', '**/.venv/**',
        'node_modules/**', '**/node_modules/**', '__pycache__/**', '**/__pycache__/**'])


class FileMapping(StrictModel):
    source: str
    target: str = ''


class Rule(StrictModel):
    name: str
    root: str = '.'
    include: list[str] = Field(min_length=1)
    exclude: list[str] = Field(default_factory=list)
    target: str = '.'


class Backup(StrictModel):
    directory: str = '../data/backups'
    scope: Literal['all', 'files', 'categories'] = 'all'


class FTPSettings(StrictModel):
    host: str
    port: int = Field(default=21, ge=1, le=65535)
    username: str
    password_env: str = 'DEPLOY_FTP_PASSWORD'
    tls: bool = False
    passive: bool = True
    timeout: int = Field(default=30, ge=1, le=120)
    encoding: str = 'utf-8'


class Deploy(StrictModel):
    method: Literal['copy', 'ftp'] = 'copy'
    destination: str = Field(validation_alias=AliasChoices('target_root', 'destination'))
    scope: Literal['all', 'files', 'categories'] = 'categories'
    categories: list[str] = Field(default_factory=list)
    overwrite: bool = True
    ftp: FTPSettings | None = None

    @model_validator(mode='before')
    @classmethod
    def ignore_removed_server_backup(cls, value):
        # Old documents still load, but can no longer enable server backups.
        if isinstance(value, dict):
            return {key: item for key, item in value.items() if key != 'backup_before_deploy'}
        return value


class Manifest(StrictModel):
    title: str = Field(min_length=1)
    project: Project
    files: list[FileMapping] = Field(default_factory=list)
    rules: list[Rule] = Field(default_factory=list)
    backup: Backup = Field(default_factory=Backup)
    deploy: Deploy | None = None


def relative_path(value, *, allow_dot=False):
    value = value.replace('\\', '/')
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or '..' in path.parts or
            any(re.search(r'[<>:"|?*\x00-\x1f]', part) for part in path.parts)):
        raise ValueError(f'프로젝트 내부 상대 경로가 필요합니다: {value}')
    if str(path) == '.' and not allow_dot:
        raise ValueError('파일 경로를 지정하세요.')
    return str(path)


def parse_manifest(markdown):
    if len(markdown.encode('utf-8')) > 2 * 1024 * 1024:
        raise ValueError('설정 문서는 2MB 이하로 작성하세요.')
    match = re.match(r'\A\ufeff?---[ \t]*\r?\n(.*?)\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|$)', markdown, re.S)
    if not match:
        raise ValueError('문서 맨 위에 YAML 프론트메터(---)가 필요합니다.')
    try:
        manifest = Manifest.model_validate(yaml.safe_load(match[1]))
    except (ValueError, yaml.YAMLError, RecursionError) as exc:
        raise ValueError(f'배포/백업 설정 오류: {exc}') from exc
    names = [rule.name for rule in manifest.rules]
    if len(names) != len(set(names)):
        raise ValueError('유형 규칙의 name이 중복되었습니다.')
    for file in manifest.files:
        relative_path(file.source)
        if file.target:
            relative_path(file.target)
    for rule in manifest.rules:
        relative_path(rule.root, allow_dot=True)
        relative_path(rule.target, allow_dot=True)
    if manifest.deploy:
        if manifest.deploy.method == 'ftp' and manifest.deploy.ftp is None:
            raise ValueError('FTP 배포에는 deploy.ftp 설정이 필요합니다.')
        destination = manifest.deploy.destination
        if not destination.strip() or any(c in destination for c in '\r\n\x00'):
            raise ValueError('배포 대상 경로를 지정하세요.')
        if manifest.deploy.method == 'ftp':
            relative_path(destination.lstrip('/') or '.', allow_dot=True)
    return manifest
