"""Round-trip local Markdown without losing its encoding or newline style."""
from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile

from app.testing.report_store import replace_with_retry


def normalize_newlines(content):
    return content.replace('\r\n', '\n').replace('\r', '\n')


@dataclass
class MarkdownFile:
    path: Path
    original: bytes

    @classmethod
    def open(cls, path):
        path = Path(path).resolve(strict=True)
        original = path.read_bytes()
        original.decode('utf-8-sig')
        return cls(path, original)

    @property
    def content(self):
        return normalize_newlines(self.original.decode('utf-8-sig'))

    def save(self, content):
        if self.path.read_bytes() != self.original:
            raise ValueError('원본 파일이 다른 프로그램에서 변경되었습니다. 파일을 다시 열어 확인한 뒤 저장하세요.')
        newline = '\r\n' if b'\r\n' in self.original else '\n'
        encoding = 'utf-8-sig' if self.original.startswith(b'\xef\xbb\xbf') else 'utf-8'
        payload = normalize_newlines(content).replace('\n', newline).encode(encoding)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix='.kja-md-', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
            shutil.copymode(self.path, temporary)
            if self.path.read_bytes() != self.original:
                raise ValueError('저장 중 원본 파일이 변경되었습니다. 파일을 다시 열어 확인하세요.')
            replace_with_retry(temporary, self.path)
            self.original = payload
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
