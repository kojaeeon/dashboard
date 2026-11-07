"""Validate executable frontmatter before starting a browser."""
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class Step(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: str
    label: str = ''
    selector: str = ''
    id: str = ''
    role: str = ''
    name: str = ''
    text: str = ''
    attr: dict[str, str] = Field(default_factory=dict)
    syscode: str = ''
    exact: bool = True
    nth: int | None = Field(default=None, ge=0)
    value: str | int | float | bool | None = None
    url: str = ''
    timeout: int | None = Field(default=None, ge=100, le=120000)

    @model_validator(mode='after')
    def validate_action(self):
        supported = {'goto', 'menu', 'click', 'dblclick', 'text', 'fill', 'select',
                     'check', 'uncheck', 'press', 'wait', 'assert_text',
                     'assert_visible', 'screenshot', 'popup', 'frame', 'main_frame'}
        if self.action not in supported:
            raise ValueError(f'지원하지 않는 action: {self.action}')
        if self.action == 'goto':
            if not (self.url or self.value):
                raise ValueError('goto: url 또는 value가 필요합니다.')
        elif self.action == 'frame':
            if not (self.selector or self.value):
                raise ValueError('frame: iframe selector 또는 value가 필요합니다.')
        elif self.action not in {'screenshot', 'main_frame'}:
            if not any((self.selector, self.id, self.role, self.label, self.text, self.attr)):
                raise ValueError(f'{self.action}: 대상을 지정하세요.')
        if self.action in {'text', 'fill', 'select', 'press', 'assert_text'} and self.value is None:
            raise ValueError(f'{self.action}: value가 필요합니다.')
        if any(not re.fullmatch(r'[A-Za-z_][\w:.-]*', key) for key in self.attr):
            raise ValueError('attr 키는 HTML 속성 이름이어야 합니다.')
        return self


class BrowserConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    base_url: str = 'http://127.0.0.1:8080'
    timeout: int = Field(default=10000, ge=100, le=120000)
    headless: bool = False


@dataclass
class Scenario:
    title: str
    work_item: dict
    browser: BrowserConfig
    steps: list[Step]


def parse_scenario(markdown: str) -> Scenario:
    if len(markdown.encode('utf-8')) > 2 * 1024 * 1024:
        raise ValueError('시나리오는 2MB 이하로 작성하세요.')
    match = re.match(r'\A\ufeff?---[ \t]*\r?\n(.*?)\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|$)', markdown, re.S)
    if not match:
        raise ValueError('문서 맨 위에 YAML 프론트메터(---)가 필요합니다.')
    try:
        metadata = yaml.safe_load(match[1])
        if not isinstance(metadata, dict):
            raise ValueError('프론트메터는 key: value 형식이어야 합니다.')
        raw_steps = metadata.get('step')
        if not isinstance(raw_steps, list) or not 1 <= len(raw_steps) <= 500:
            raise ValueError('step에 1~500개 단계가 필요합니다.')
        steps = [Step.model_validate(step) for step in raw_steps]
        browser = BrowserConfig.model_validate(metadata.get('browser', {}))
        validate_base_url(browser.base_url)
        work_item = metadata.get('workItem', {})
        if not isinstance(work_item, dict):
            raise ValueError('workItem은 key: value 형식이어야 합니다.')
        title = metadata.get('title') or work_item.get('serviceNm') or work_item.get('menu') or 'UI 시나리오'
        return Scenario(str(title), work_item, browser, steps)
    except (yaml.YAMLError, ValidationError, RecursionError) as exc:
        raise ValueError(f'프론트메터 검증 실패: {exc}') from exc


def validate_base_url(value):
    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise ValueError('시작 URL은 http:// 또는 https:// 주소여야 합니다.')
    return value
