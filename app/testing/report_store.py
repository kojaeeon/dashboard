"""Publish complete JSON snapshots, tolerating short Windows reader locks."""
import json
import os
from pathlib import Path
import tempfile
import time


def replace_with_retry(source, destination, *, retry_seconds=3):
    deadline = time.monotonic() + retry_seconds
    delay = .01
    while True:
        try:
            os.replace(source, destination)
            return
        except PermissionError:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise
            time.sleep(min(delay, remaining))
            delay = min(delay * 2, .1)


def write_report(path: Path, report, *, retry_seconds=3):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix=path.name + '.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(report, stream, ensure_ascii=False, indent=2)
        # Retrying persistence never repeats a browser action.
        replace_with_retry(temporary, path, retry_seconds=retry_seconds)
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
