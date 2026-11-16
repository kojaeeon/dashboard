"""Frontmatter configuration for ZIP backups."""
from pathlib import PurePosixPath
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
import yaml


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)


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


class Sftp(StrictModel):
    host: str = Field(min_length=1)
    port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(min_length=1)
    password: SecretStr | None = None
    private_key: str | None = None
    passphrase: SecretStr | None = None
    known_hosts: str | None = None
    timeout: float = Field(default=30, gt=0, le=300)


class Manifest(StrictModel):
    title: str = Field(min_length=1)
    project: Project
    files: list[FileMapping] = Field(default_factory=list)
    rules: list[Rule] = Field(default_factory=list)
    backup: Backup = Field(default_factory=Backup)
    sftp: Sftp | None = None

    @model_validator(mode='before')
    @classmethod
    def ignore_legacy_deploy(cls, value):
        # Existing project documents remain usable; no deployment config is read.
        if isinstance(value, dict):
            return {key: item for key, item in value.items() if key != 'deploy'}
        return value


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
        raise ValueError(f'백업 설정 오류: {exc}') from exc
    names = [rule.name for rule in manifest.rules]
    if len(names) != len(set(names)):
        raise ValueError('유형 규칙의 name이 중복되었습니다.')
    for file in manifest.files:
        relative_path(file.source)
    for rule in manifest.rules:
        relative_path(rule.root, allow_dot=True)
    return manifest
