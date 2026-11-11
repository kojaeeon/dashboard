"""Read code generation inputs from workItem frontmatter."""
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.common.database import Database

MAX_MD_SIZE = 2 * 1024 * 1024
FIELD_MAP = {
    'table': 'table_name',
    'service': 'service_name',
    'serviceNm': 'service_korean_name',
    'package': 'package_path',
}


@dataclass(frozen=True)
class MarkdownSource:
    key: str
    label: str
    location: str
    content: str | None = None
    path: Path | None = None

    def read(self) -> str:
        if self.path is not None:
            if self.path.stat().st_size > MAX_MD_SIZE:
                raise ValueError('2MB 이하 MD 파일만 지원합니다.')
            return self.path.read_text(encoding='utf-8-sig')
        return self.content or ''


def markdown_sources(db: Database) -> tuple[list[MarkdownSource], list[str]]:
    sources = [MarkdownSource(f"document:{d['id']}", f"[저장 문서] {d['title']}",
                              'MD 보기 · 저장 문서', content=d['content'])
               for d in db.list('documents')]
    warnings = []
    seen = set()
    for folder in db.folders():
        root = Path(folder['path'])
        try:
            if not root.is_dir():
                raise OSError('폴더가 없거나 접근할 수 없습니다.')
            for path in sorted(root.rglob('*')):
                if path.suffix.lower() not in {'.md', '.markdown'} or not path.is_file():
                    continue
                resolved = path.resolve()
                if not resolved.is_relative_to(root.resolve()) or resolved in seen:
                    continue
                seen.add(resolved)
                sources.append(MarkdownSource(f'file:{resolved}',
                                              f'[{root.name}] {path.relative_to(root)}',
                                              str(resolved), path=resolved))
        except OSError as exc:
            warnings.append(f'{root}: {exc}')
    return sources, warnings


def read_work_item(content: str) -> dict[str, str]:
    if len(content.encode('utf-8')) > MAX_MD_SIZE:
        raise ValueError('2MB 이하 MD 파일만 지원합니다.')
    lines = content.lstrip('\ufeff').splitlines()
    if not lines or lines[0].strip() != '---':
        raise ValueError('문서 시작에 YAML 프론트매터(---)가 필요합니다.')
    end = next((i for i in range(1, len(lines)) if lines[i].strip() in {'---', '...'}), None)
    if end is None:
        raise ValueError('프론트매터 닫는 구분자(---)가 없습니다.')
    try:
        metadata = yaml.safe_load('\n'.join(lines[1:end]))
    except yaml.YAMLError as exc:
        raise ValueError('프론트매터 YAML 형식을 확인하세요.') from exc
    item = metadata.get('workItem') if isinstance(metadata, dict) else None
    if not isinstance(item, dict):
        raise ValueError('프론트매터에 workItem 항목이 필요합니다.')
    result = {}
    for source, target in FIELD_MAP.items():
        value = item.get(source)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'workItem.{source}에 문자열 값을 입력하세요.')
        result[target] = value.strip()
    return result


def work_item_yaml(values: dict[str, str]) -> str:
    # Show only generation inputs, not unrelated deploy/connection metadata.
    return yaml.safe_dump({'workItem': {key: values[value] for key, value in FIELD_MAP.items()}},
                          allow_unicode=True, sort_keys=False)
