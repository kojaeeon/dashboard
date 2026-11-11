import pytest
from app.common.markdown_file import MarkdownFile


@pytest.mark.parametrize('bom,newline', [(b'', '\n'), (b'', '\r\n'), (b'\xef\xbb\xbf', '\r\n')])
def test_local_markdown_roundtrip_keeps_format(tmp_path, bom, newline):
    path = tmp_path / 'document.md'
    path.write_bytes(bom + ('---\ntitle: 예시\n---\n# 원문\n').replace('\n', newline).encode('utf-8'))
    document = MarkdownFile.open(path)
    assert '\r' not in document.content
    content = '---\ntitle: 수정\n---\n# 변경\n```python\nprint("한글 😀")\n```\n'
    document.save(content)
    assert path.read_bytes() == bom + content.replace('\n', newline).encode('utf-8')
    document.save(content + '\n다시 저장\n')
    assert MarkdownFile.open(path).content == content + '\n다시 저장\n'
    assert not list(tmp_path.glob('.kja-md-*'))


def test_external_edit_is_not_overwritten(tmp_path):
    path = tmp_path / 'document.md'
    path.write_text('# Original', encoding='utf-8')
    document = MarkdownFile.open(path)
    path.write_text('# Changed elsewhere', encoding='utf-8')
    with pytest.raises(ValueError, match='다른 프로그램'):
        document.save('# My changes')
    assert path.read_text(encoding='utf-8') == '# Changed elsewhere'
