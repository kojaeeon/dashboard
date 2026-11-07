"""Separate-process runner keeps browser lifecycle independent of NiceGUI."""
import argparse
import asyncio
from pathlib import Path
import time

from playwright.async_api import async_playwright
from app.common.ui_accelerator import PlaywrightAccelerator
from app.testing.scenario import parse_scenario
from app.testing.report_store import write_report


async def execute_file(source, output, base_url=None, headed=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    scenario = parse_scenario(Path(source).read_text(encoding='utf-8-sig'))
    report = {'title': scenario.title, 'status': 'running', 'error': '', 'steps': [
        {'number': i, 'action': s.action, 'target': s.label or s.name or s.selector or s.id or s.text,
         'status': 'pending', 'duration_ms': 0, 'strategy': '', 'error': ''}
        for i, s in enumerate(scenario.steps, 1)]}

    def publish():
        write_report(output / 'result.json', report)

    publish()

    async def run_browser():
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=scenario.browser.headless if headed is None else not headed)
            context = None
            current = None
            try:
                context = await browser.new_context(viewport={'width': 1440, 'height': 1000})
                await context.tracing.start(screenshots=True, snapshots=True, sources=True)
                page = await context.new_page()
                accelerator = PlaywrightAccelerator(
                    page, base_url=base_url or scenario.browser.base_url,
                    output_dir=output, timeout=scenario.browser.timeout)
                await page.goto(accelerator.base_url, wait_until='domcontentloaded', timeout=scenario.browser.timeout)
                for step, current in zip(scenario.steps, report['steps']):
                    current['status'] = 'running'
                    publish()
                    started = time.monotonic()
                    try:
                        current['strategy'] = await accelerator.execute(step, current['number'])
                        current['status'] = 'passed'
                    except asyncio.CancelledError:
                        current['status'] = 'cancelled'
                        raise
                    except Exception as exc:
                        current['status'] = 'failed'
                        current['error'] = str(exc)
                        try:
                            await accelerator.page.screenshot(path=str(output / 'failure.png'), full_page=True, timeout=5000)
                        except Exception:
                            pass
                        raise
                    finally:
                        current['duration_ms'] = round((time.monotonic() - started) * 1000)
                        publish()
                await accelerator.page.screenshot(path=str(output / 'final.png'), full_page=True)
                report['status'] = 'passed'
            finally:
                try:
                    if context is not None:
                        await context.tracing.stop(path=str(output / 'trace.zip'))
                finally:
                    await browser.close()

    async def wait_stop():
        while not (output / 'stop').exists():
            await asyncio.sleep(.2)

    browser_task = asyncio.create_task(run_browser())
    stop_task = asyncio.create_task(wait_stop())
    try:
        done, _ = await asyncio.wait({browser_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
        if stop_task in done and not browser_task.done():
            browser_task.cancel()
            try:
                await browser_task
            except asyncio.CancelledError:
                pass
            report['status'] = 'cancelled'
        else:
            await browser_task
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = str(exc)
    finally:
        stop_task.cancel()
        for step in report['steps']:
            if step['status'] == 'pending':
                step['status'] = 'skipped'
        publish()
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--base-url')
    parser.add_argument('--headed', action='store_true')
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()
    try:
        report = asyncio.run(execute_file(args.scenario, args.output, args.base_url,
                                        True if args.headed else False if args.headless else None))
        return 0 if report['status'] == 'passed' else 1
    except Exception as exc:
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)
        write_report(output / 'result.json',
                     {'status': 'failed', 'error': str(exc), 'steps': []})
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
