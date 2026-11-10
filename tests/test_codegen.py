from io import BytesIO
from zipfile import ZipFile

import pytest
from nicegui import ui

from app.codegen.service import GeneratedFile, GenerationRequest, PreviewGenerator, build_zip
from app.common.database import Database


def test_preview_zip_preserves_paths_and_utf8():
    request = GenerationRequest('KAML.TB_CRA', 'CraInspection', 'CRA 정기점검', 'com.kaml.cra')
    files = PreviewGenerator().generate(request)
    assert len(files) == 4
    with ZipFile(BytesIO(build_zip(files))) as archive:
        assert archive.namelist() == [f.path for f in files]
        for file in files:
            assert archive.read(file.path).decode('utf-8') == file.content
    assert 'CRA 정기점검' in files[0].content


@pytest.mark.parametrize('path', ['../bad.java', '/bad.java', 'C:/bad.java', 'a\\bad.java'])
def test_invalid_output_paths(path):
    with pytest.raises(ValueError):
        build_zip([GeneratedFile(path, '')])


def test_request_validation_and_target_selection():
    with pytest.raises(ValueError):
        PreviewGenerator().generate(GenerationRequest('TB_CRA', '../bad', '점검', 'com.example'))
    files = PreviewGenerator().generate(GenerationRequest('TB_CRA', 'Cra', '점검', 'com.example', ('VO',)))
    assert [f.path for f in files] == ['src/main/java/com/example/CraVO.java']


@pytest.mark.asyncio
async def test_preview_download_and_invalidation(user, tmp_path, monkeypatch):
    from app.pages import code_gen
    downloads = []
    monkeypatch.setattr(ui, 'download', lambda data, **kwargs: downloads.append((data, kwargs)))

    @ui.page('/code-gen-test')
    def page():
        code_gen.render(Database(str(tmp_path / 'test.db')))

    await user.open('/code-gen-test')
    button = next(iter(user.find(marker='code-gen-download').elements))
    assert not button.enabled
    user.find(kind=ui.input, content='테이블명 *').type('KAML.TB_CRA')
    user.find(kind=ui.input, content='서비스명 *').type('CraInspection')
    user.find(kind=ui.input, content='서비스 한글명 *').type('CRA 정기점검')
    user.find(kind=ui.input, content='패키지 경로 *').type('com.kaml.cra')
    user.find(marker='code-gen-preview').click()
    await user.should_see('4개 파일')
    await user.should_see('샘플 미리보기 · 실제 생성 서비스 연결 전')
    assert button.enabled
    user.find(marker='code-gen-download').click()
    assert downloads[0][1]['filename'] == 'CraInspection.zip'
    with ZipFile(BytesIO(downloads[0][0])) as archive:
        assert len(archive.namelist()) == 4
    user.find(kind=ui.input, content='서비스명 *').type('Next')
    await user.should_see('0개 파일')
    assert not button.enabled
