import pytest
from nicegui import ui

from app.codegen.frontmatter import markdown_sources, read_work_item, work_item_yaml
from app.common.database import Database

MD = '''---
workItem:
  menu: "CDD > 개인 > 체크리스트"
  service: "CddBc1Qry"
  serviceNm: "BC1질의서"
  table: "KAML.CDD_BC1_INQRY_DOC"
  package: "com.kaml.cdd"
deploy:
  secret: hidden
---
# 업무 문서
'''


def test_exact_workitem_mapping():
    values = read_work_item('\ufeff' + MD)
    assert values == dict(table_name='KAML.CDD_BC1_INQRY_DOC', service_name='CddBc1Qry',
                          service_korean_name='BC1질의서', package_path='com.kaml.cdd')
    assert 'hidden' not in work_item_yaml(values)
    assert 'serviceNm: BC1질의서' in work_item_yaml(values)


@pytest.mark.parametrize('text', ['# no frontmatter', '---\nworkItem: {}',
                                 '---\nworkItem: []\n---',
                                 '---\nworkItem: {table: 12}\n---',
                                 '---\nworkItem: [\n---'])
def test_invalid_frontmatter(text):
    with pytest.raises(ValueError):
        read_work_item(text)


def test_saved_and_nested_local_markdown(tmp_path):
    db = Database(str(tmp_path / 'db.sqlite'))
    db.save_document('저장 문서', MD)
    root = tmp_path / 'docs'
    nested = root / 'scenarios'
    nested.mkdir(parents=True)
    (nested / 'example.md').write_text(MD, encoding='utf-8-sig')
    db.add_folder(str(root))
    db.add_folder(str(nested))
    sources, warnings = markdown_sources(db)
    assert not warnings
    assert len(sources) == 2  # Overlapping registered folders do not duplicate files.
    for source in sources:
        assert read_work_item(source.read())['service_name'] == 'CddBc1Qry'


@pytest.mark.asyncio
async def test_md_selection_fills_inputs_and_invalidates_zip(user, tmp_path):
    from app.pages.code_gen import render
    db = Database(str(tmp_path / 'ui.sqlite'))
    db.save_document('BC1질의서', MD)
    db.save_document('잘못된 문서', '---\nworkItem: {}\n---')
    db.save_document('다른 문서', MD.replace('CddBc1Qry', 'OtherService'))

    @ui.page('/code-gen-md-test')
    def page():
        render(db)

    await user.open('/code-gen-md-test')
    await user.should_see('MD 3개 · 선택하면 생성 정보가 자동 입력됩니다.')
    user.find(marker='code-gen-md').click()
    user.find('[저장 문서] BC1질의서').click()
    await user.should_see('생성 정보 4개를 자동 입력했습니다. 입력값은 직접 수정할 수 있습니다.')
    fields = {e.label: e for e in user.find(kind=ui.input).elements}
    assert fields['테이블명 *'].value == 'KAML.CDD_BC1_INQRY_DOC'
    assert fields['서비스명 *'].value == 'CddBc1Qry'
    assert fields['서비스 한글명 *'].value == 'BC1질의서'
    assert fields['패키지 경로 *'].value == 'com.kaml.cdd'
    user.find(marker='code-gen-preview').click()
    await user.should_see('4개 파일')
    user.find(marker='code-gen-md').click()
    user.find('[저장 문서] 다른 문서').click()
    await user.should_see('0개 파일')
    assert fields['서비스명 *'].value == 'OtherService'
    assert not next(iter(user.find(marker='code-gen-download').elements)).enabled
    user.find(marker='code-gen-md').click()
    user.find('[저장 문서] 잘못된 문서').click()
    await user.should_see('자동 입력 실패: workItem.table에 문자열 값을 입력하세요.')
    assert fields['서비스명 *'].value == 'OtherService'
