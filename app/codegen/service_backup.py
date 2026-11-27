"""사진에서 옮긴 코드젠 백업입니다. 대시보드 앱에서는 이 파일을 사용하지 않습니다."""

# 원본 사진에서 가려진 부분과 저장소 코드를 참고해 복원한 부분을 주석으로 표시했습니다.
from dataclasses import asdict, dataclass
# 원본 3~11행은 접혀 있습니다. 확인 가능한 참조를 기준으로 표준/Jinja2 import를 복원했습니다.
from io import BytesIO
from pathlib import Path, PurePosixPath
import re
from typing import Protocol
from zipfile import ZIP_DEFLATED, ZipFile

from jinja2 import DictLoader, Environment, FileSystemLoader, StrictUndefined

# DB 클래스의 원본 import 경로는 사진에서 확인할 수 없습니다.

TEMPLATE_DIR = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "template"
    / "code"
)

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    keep_trailing_newline=True,
)

gen_item_1 = "VO"
gen_item_2 = "Mapper XML"
gen_item_3 = "DAO"
gen_item_4 = "Service/impl (4종)"
gen_item_5 = "Controller"

# 원본 31행 오른쪽 끝이 잘려 선언된 생성 대상 다섯 개로 튜플을 완성했습니다.
TARGETS = (gen_item_1, gen_item_2, gen_item_3, gen_item_4, gen_item_5)


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


# 인라인 샘플 문자열(원본 71~72행)의 잘린 뒷부분은 저장소 service.py에서 복원했습니다.
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
        # 여기부터 GEN CODE
        df = fn_data_gen(request)
        columns = df.to_dict("records")
        directory = f"docs/output"
        for target in request.targets:
            xml = None
            if target == gen_item_1:
                # VO
                template = jinja_env.get_template("vo.java.j2")
                source = template.render(
                    info=request,
                    columns=columns,
                )
                filename = f"""{request.service_name}Vo.java"""
                files.append(GeneratedFile(f'{directory}/{filename}', source, 'xml' if xml else 'java'))
            if target == gen_item_2:
                # Mapper XML
                template = jinja_env.get_template("templateDao.xml.j2")
                queryMap = gen_query(request, columns)
                source = template.render(
                    info=request,
                    maps=queryMap,
                )
                filename = f"""{request.service_name}Dao.xml"""
                files.append(GeneratedFile(f'{directory}/{filename}', source, 'xml' if xml else 'java'))
            if target == gen_item_5:
                # Controller
                template = jinja_env.get_template("ctl.java.j2")
                source = template.render(
                    info=request,
                    columns=columns,
                )
                filename = f"""{request.service_name}Ctl.java"""
                files.append(GeneratedFile(f'{directory}/{filename}', source, 'xml' if xml else 'java'))

        # END
        # for target in request.targets:
        #     xml = target == 'Mapper'
        #     filename = f'{request.service_name}{target}' + ('.xml' if xml else '.java')
        #     directory = 'src/main/resources/mappers' if xml else 'src/main/java/' + request.package_path.replace('.', '/')
        #
        #     #content = env.get_template('xml' if xml else 'java').render(**context, target=target)
        #     content = env.get_template('xml' if xml else 'java').render(**context, target=target)
        # 원본 120~140행은 사진에 없습니다. 반환문과 ZIP 함수는 저장소 service.py를 참고했습니다.
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


def fn_data_gen(request):
    # 메타 쿼리 부터 조회
    tableId = request.table_name
    if "." not in tableId:
        raise ValueError('테이블명은 테이블 또는 스키마.테이블 형식으로 입력하세요.')
    testDb = DB("devAis")
    TABSCHEMA, TABNAME = tableId.split(".", 1)
    meta_sql = f"""
                    SELECT
                        C.TABSCHEMA
                        ,C.TABNAME
                        ,C.COLNO
                        ,C.COLNAME
                        ,C.REMARKS
                        ,C.TYPENAME
                        ,C."LENGTH"
                        ,C."SCALE"
                        ,C.NULLS
                        ,C."DEFAULT"
                        ,CASE WHEN k.COLNAME IS NOT NULL THEN 'Y' ELSE 'N' END AS PK_YN
                    FROM SYSCAT.columns C
                    LEFT JOIN SYSCAT.keycoluse k
                    ON k.TABSCHEMA = C.TABSCHEMA
                    AND k.TABNAME = C.TABNAME
                    AND k.COLNAME = C.COLNAME
                    WHERE C.TABSCHEMA = '{TABSCHEMA}'
                    AND C.TABNAME ='{TABNAME}'
                    ORDER BY TABNAME,C.colno
            """
    print(f"query : {meta_sql}")
    df = testDb.query_df(meta_sql)
    # 원본 174~177행은 가려져 있습니다. CAMEL_NAME 대입은 아래 사용처로부터 추정했습니다.
    df["CAMEL_NAME"] = df["COLNAME"].map(to_camel)
    df["JAVA_TYPE"] = df.apply(to_java_type, axis=1)

    return df


def fn_gen_source(matter, genInfo):
    #df.to_excel("docs/output/output.xlsx", sheet_name=TABNAME, index=False)
    #print(jinja_env.list_templates())

    outputPath = Path("docs/output")
    targets = genInfo["targets"]
    columns = df.to_dict("records")
    for target in targets:
        # VO
        if target == gen_item_1:
            template = jinja_env.get_template("vo.java.j2")
            source = template.render(
                info=genInfo,
                columns=columns,
            )
            filename = f"""{genInfo["service"]}Vo.java"""
            to_outFile(outputPath, filename, source)

        # sql_xml
        if target == gen_item_2:
            template = jinja_env.get_template("templateDao.xml.j2")
            queryMap = gen_query(genInfo, columns)
            source = template.render(
                info=genInfo,
                maps=queryMap,
            )
            filename = f"""{genInfo["service"]}Dao.xml"""
            to_outFile(outputPath, filename, source)


def to_outFile(path, filename, source):
    fullPath = path / filename
    fullPath.write_text(source, encoding="utf-8")


def to_java_type(row):
    db_type = str(row["TYPENAME"]).upper()

    if db_type in ("CHARACTER", "CHAR", "VARCHAR", "CLOB"):
        return "String"

    if db_type in ("INTEGER", "SMALLINT"):
        return "Integer"

    if db_type in ("DECIMAL", "NUMERIC"):
        return "BigDecimal"

    if db_type == "DATE":
        # vo 체크 결과 String 으로 받고 있음
        return "String"

    if db_type == "TIMESTAMP":
        return "java.util.Date"


def gen_query(genInfo, columns):
    result = {}
    # 공통컬럼은 insert, update 시 변경 => INIT_REGIST_TMP, LST_CHNG_TMP
    cmn_col = ["INIT_REGIST_TMP", "LST_CHNG_TMP"]  # => CURRENT_TIMESTAMP

    head_select = "SELECT \n"
    head_insert = f"""INSERT INTO {genInfo.table_name} ( \n"""
    head_update = f"""UPDATE {genInfo.table_name} \n SET \n"""

    body_select = []
    body_insert = []
    body_insert2 = []
    body_update = []

    pk_array = []
    # body_select.append(f""" {col["COLNAME"]} """)
    idx = 0
    for col in columns:
        if idx == 0:
            print(f"{idx} : {col['REMARKS']}")
            body_select.append(f"""\t {str(col["COLNAME"]).ljust(35)} /* {col["REMARKS"]} */ """)
            body_insert.append(f"""\t {str(col["COLNAME"]).ljust(35)} /* {col["REMARKS"]} */ """)
            body_insert2.append(f"""\t #{{{col["CAMEL_NAME"]}}} """)
            body_update.append(f"""\t {col["COLNAME"]} = #{{{col["CAMEL_NAME"]}}}""")
        if idx != 0:
            body_select.append(f"""\t ,{str(col["COLNAME"]).ljust(35)} /* {col["REMARKS"]} */ """)
            body_insert.append(f"""\t ,{str(col["COLNAME"]).ljust(35)} /* {col["REMARKS"]} */ """)
            body_insert2.append(f"""\t ,#{{{col["CAMEL_NAME"]}}} """)
            body_update.append(f"""\t ,{col["COLNAME"]} = #{{{col["CAMEL_NAME"]}}}""")
        if col["PK_YN"] == 'Y':
            # 원본 265행은 가려져 있습니다. 아래 pk_array 사용처로부터 추정했습니다.
            pk_array.append(col)
        idx = idx + 1

    end_select = f""" \n FROM {genInfo.table_name} \n WHERE 1=1 """
    for vo_pk in pk_array:
        end_select = end_select + f"""\n AND {vo_pk["COLNAME"]} = #{{{col["CAMEL_NAME"]}}}"""

    end_update = f""" \n WHERE 1=1 """
    for vo_pk in pk_array:
        end_update = end_update + f"""\n AND {vo_pk["COLNAME"]} = #{{{col["CAMEL_NAME"]}}}"""

    end_delete = f""" \n DELETE FROM \n {genInfo.table_name} \n WHERE 1=1 """
    for vo_pk in pk_array:
        end_delete = end_delete + f"""\n AND {vo_pk["COLNAME"]} = #{{{col["CAMEL_NAME"]}}}"""

    end_select = end_select + "\n WITH UR"

    select_qry = head_select + "\n".join(body_select) + end_select
    insert_qry = head_insert + "\n".join(body_insert) + "\n ) VALUES ( \n" + "\n".join(body_insert2) + ") \n"
    update_qry = head_update + "\n".join(body_update) + end_update
    delete_qry = end_delete

    result["select_sql"] = select_qry
    result["insert_sql"] = insert_qry
    result["update_sql"] = update_qry
    result["delete_sql"] = delete_qry
    return result


def to_camel(s):
    parts = str(s).lower().split("_")
    return parts[0] + "".join(x.capitalize() for x in parts[1:])
