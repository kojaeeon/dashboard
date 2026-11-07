import json
import os
from pathlib import Path
from threading import Thread
import time

import pytest

from app.testing.report_store import write_report


def test_transient_lock_retries_only_publish(tmp_path, monkeypatch):
    path = tmp_path / 'result.json'
    write_report(path, {'status': 'running'})
    replace = os.replace
    attempts = 0

    def locked_replace(source, destination):
        nonlocal attempts
        attempts += 1
        if attempts < 4:
            assert json.loads(path.read_text()) == {'status': 'running'}
            raise PermissionError('sharing violation')
        replace(source, destination)

    monkeypatch.setattr(os, 'replace', locked_replace)
    write_report(path, {'status': 'passed'})
    assert attempts == 4
    assert json.loads(path.read_text()) == {'status': 'passed'}
    assert not list(tmp_path.glob('*.tmp'))


def test_permanent_lock_preserves_previous_report(tmp_path, monkeypatch):
    path = tmp_path / 'result.json'
    write_report(path, {'status': 'running'})

    def locked_replace(*_):
        raise PermissionError('locked')

    monkeypatch.setattr(os, 'replace', locked_replace)
    with pytest.raises(PermissionError):
        write_report(path, {'status': 'passed'}, retry_seconds=.02)
    assert json.loads(path.read_text()) == {'status': 'running'}
    assert not list(tmp_path.glob('*.tmp'))


@pytest.mark.skipif(os.name != 'nt', reason='Windows file sharing semantics')
def test_windows_open_reader_lock_is_retried(tmp_path):
    import ctypes
    from ctypes import wintypes

    path = tmp_path / 'result.json'
    write_report(path, {'status': 'running'})
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    # Share reads, but deliberately deny deletion/rename like an open reader.
    handle = kernel.CreateFileW(str(path), 0x80000000, 1, None, 3, 0x80, None)
    assert handle != wintypes.HANDLE(-1).value

    def release():
        time.sleep(.15)
        kernel.CloseHandle(handle)

    thread = Thread(target=release)
    thread.start()
    try:
        write_report(path, {'status': 'passed'})
    finally:
        thread.join()
    assert json.loads(path.read_text()) == {'status': 'passed'}
