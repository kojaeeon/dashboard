"""Replace PreviewGenerator with the real metadata/template service."""
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import PurePosixPath
import re
from typing import Protocol
from zipfile import ZIP_DEFLATED, ZipFile

from jinja2 import DictLoader, Environment, StrictUndefined


TARGETS = ('Controller', 'Service', 'VO', 'Mapper')


@dataclass(frozen=True)
class GenerationRequest:
    table_name: str
    service_name: str
    service_korean_name: str
    package_path: str
    targets: tuple[str, ...] = TARGETS

    def validate(self):
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?', self.table_name):
            raise ValueError('테이블명은 테이블 또는 스키마.테이블 형식으로 입력하세요.')
        if not re.fullmatch(r'[A-Z][A-Za-z0-9_]*', self.service_name):
            raise ValueError('서비스명은 영문 대문자로 시작하는 클래스명으로 입력하세요.')
        if not self.service_korean_name.strip():
            raise ValueError('서비스 한글명을 입력하세요.')
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*', self.package_path):
            raise ValueError('패키지 경로는 com.example.service 형식으로 입력하세요.')
        if not self.targets or len(set(self.targets)) != len(self.targets) or any(t not in TARGETS for t in self.targets):
            raise ValueError('생성 대상을 하나 이상 선택하세요.')


@dataclass(frozen=True)
class GeneratedFile:
    path: str  # Project-relative path, also used as ZIP entry name.
    content: str
    language: str = 'java'


class CodeGenerator(Protocol):
    def generate(self, request: GenerationRequest) -> list[GeneratedFile]: ...


class PreviewGenerator:
    """UI-only Jinja2 samples; no DB metadata lookup or production generation."""
    def generate(self, request: GenerationRequest) -> list[GeneratedFile]:
        request.validate()
        env = Environment(loader=DictLoader({
            'java': 'package {{ package_path }};\n\n// 샘플: {{ service_korean_name | comment }}\n// 대상 테이블: {{ table_name }}\npublic class {{ service_name }}{{ target }} {\n    // 실제 생성 서비스 연결 영역\n}\n',
            'xml': '<?xml version="1.0" encoding="UTF-8"?>\n<!-- 샘플 Mapper: 실제 SQL 생성 서비스 연결 전 -->\n<mapper namespace="{{ package_path }}.{{ service_name }}Mapper">\n    <!-- 대상 테이블: {{ table_name }} -->\n</mapper>\n',
        }), undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True)
        env.filters['comment'] = lambda value: ' '.join(value.splitlines())
        context = asdict(request)
        files = []
        for target in request.targets:
            xml = target == 'Mapper'
            filename = f'{request.service_name}{target}' + ('.xml' if xml else '.java')
            directory = 'src/main/resources/mappers' if xml else 'src/main/java/' + request.package_path.replace('.', '/')
            content = env.get_template('xml' if xml else 'java').render(**context, target=target)
            files.append(GeneratedFile(f'{directory}/{filename}', content, 'xml' if xml else 'java'))
        return files


def build_zip(files: list[GeneratedFile]) -> bytes:
    """UTF-8 ZIP of precisely the previewed files, without writing server files."""
    if not files:
        raise ValueError('다운로드할 생성 파일이 없습니다.')
    names = set()
    buffer = BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:
        for file in files:
            path = PurePosixPath(file.path)
            if not file.path or path.is_absolute() or '..' in path.parts or '\\' in file.path or ':' in file.path or str(path) == '.':
                raise ValueError('생성 파일 경로는 프로젝트 내부 상대 경로여야 합니다.')
            name = str(path)
            if name in names:
                raise ValueError('중복된 생성 파일 경로입니다.')
            names.add(name)
            archive.writestr(name, file.content.encode('utf-8'))
    return buffer.getvalue()
