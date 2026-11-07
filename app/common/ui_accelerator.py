"""Reusable Playwright actions; choose a locator before performing an action."""
import asyncio
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.async_api import expect
from app.testing.scenario import Step


class PlaywrightAccelerator:
    def __init__(self, page, *, base_url, output_dir: Path, timeout=10000):
        self.page = page
        self.scope = page
        self.base_url = base_url.rstrip('/') + '/'
        self.output_dir = output_dir
        self.timeout = timeout

    def candidates(self, step: Step):
        scope = self.scope
        # Explicit selectors are authoritative. Semantic fallbacks only resolve
        # a target; failed clicks are never replayed with another locator.
        if step.selector:
            return [('selector', scope.locator(step.selector))]
        if step.id:
            return [('id', scope.locator(f'[id={json.dumps(step.id)}]'))]
        if step.attr:
            selector = ''.join(f'[{key}={json.dumps(value)}]' for key, value in step.attr.items())
            return [('attr', scope.locator(selector))]
        if step.syscode:
            return [('syscode', scope.locator(f'[syscode={json.dumps(step.syscode)}]'))]
        if step.role:
            name = step.name or step.label
            return [('role', scope.get_by_role(step.role, **({'name': name, 'exact': step.exact} if name else {})))]
        candidates = []
        if step.label:
            candidates.append(('label', scope.get_by_label(step.label, exact=step.exact)))
        text = step.text or step.label
        if text:
            candidates.append(('text', scope.get_by_text(text, exact=step.exact)))
        return candidates

    async def locate(self, step):
        deadline = time.monotonic() + (step.timeout or self.timeout) / 1000
        while True:
            for strategy, locator in self.candidates(step):
                visible = locator.filter(visible=True)
                count = await visible.count()
                if step.nth is not None:
                    if count > step.nth:
                        return strategy, visible.nth(step.nth)
                elif count == 1:
                    return strategy, visible
                elif count > 1:
                    raise ValueError(f'{strategy}: 보이는 대상이 {count}개입니다. selector / role / nth로 구분하세요.')
            if time.monotonic() >= deadline:
                raise TimeoutError(f'대상을 찾지 못했습니다: {step.label or step.selector or step.id or step.text or step.role}')
            await asyncio.sleep(.1)

    async def execute(self, step: Step, number: int):
        timeout = step.timeout or self.timeout
        action = step.action
        if action == 'goto':
            url = urljoin(self.base_url, str(step.url or step.value))
            if urlparse(url).scheme not in {'http', 'https'}:
                raise ValueError('goto는 HTTP(S) 주소만 지원합니다.')
            await self.page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            self.scope = self.page
            return 'url'
        if action == 'frame':
            self.scope = self.page.frame_locator(str(step.selector or step.value))
            return 'frame'
        if action == 'main_frame':
            self.scope = self.page
            return 'main_frame'
        if action == 'screenshot':
            await self.page.screenshot(path=str(self.output_dir / f'{number:03d}-screenshot.png'), full_page=True)
            return 'screenshot'
        strategy, locator = await self.locate(step)
        if action in {'click', 'menu'}:
            await locator.click(timeout=timeout)
        elif action == 'dblclick':
            await locator.dblclick(timeout=timeout)
        elif action in {'text', 'fill'}:
            await locator.fill(str(step.value), timeout=timeout)
        elif action == 'select':
            await locator.select_option(str(step.value), timeout=timeout)
        elif action == 'check':
            await locator.check(timeout=timeout)
        elif action == 'uncheck':
            await locator.uncheck(timeout=timeout)
        elif action == 'press':
            await locator.press(str(step.value), timeout=timeout)
        elif action in {'wait', 'assert_visible'}:
            await expect(locator).to_be_visible(timeout=timeout)
        elif action == 'assert_text':
            await expect(locator).to_contain_text(str(step.value), timeout=timeout)
        elif action == 'popup':
            async with self.page.expect_popup(timeout=timeout) as info:
                await locator.click(timeout=timeout)
            self.page = await info.value
            await self.page.wait_for_load_state('domcontentloaded', timeout=timeout)
            self.scope = self.page
        return strategy
