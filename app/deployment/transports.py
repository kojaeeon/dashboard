"""Local copy and FTP implementations for the same reviewed file plan."""
from ftplib import FTP, FTP_TLS, error_perm
import os
from pathlib import PurePosixPath
import shutil
import tempfile
from uuid import uuid4

from app.deployment.planner import checked_child
from app.testing.report_store import replace_with_retry


class CopyTransport:
    def __init__(self, root):
        self.root = root

    def __enter__(self):
        self.root.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, *args):
        pass

    def exists(self, relative):
        return checked_child(self.root, relative).exists()

    def write_from(self, relative, source):
        target = checked_child(self.root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.kja-', delete=False) as output:
                temporary = output.name
                shutil.copyfileobj(source, output)
            replace_with_retry(temporary, target)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)


class FTPTransport:
    def __init__(self, settings, destination):
        self.settings = settings
        self.destination = destination
        self.ftp = None

    def __enter__(self):
        settings = self.settings
        if settings.password_env and settings.password_env not in os.environ:
            raise ValueError(f'FTP 비밀번호 환경변수를 설정하세요: {settings.password_env}')
        ftp = FTP_TLS(encoding=settings.encoding) if settings.tls else FTP(encoding=settings.encoding)
        self.ftp = ftp
        try:
            ftp.connect(settings.host, settings.port, timeout=settings.timeout)
            ftp.login(settings.username, os.getenv(settings.password_env, ''))
            if settings.tls:
                ftp.prot_p()
            ftp.set_pasv(settings.passive)
            if self.destination.startswith('/'):
                ftp.cwd('/')
            self._mkdirs(self.destination)
            self.root = ftp.pwd()
            return self
        except BaseException:
            ftp.close()
            raise

    def __exit__(self, *args):
        self.ftp.close()

    def _mkdirs(self, directory):
        for part in PurePosixPath(directory).parts:
            if part in {'/', '.'}:
                continue
            try:
                self.ftp.cwd(part)
            except error_perm as exc:
                if not str(exc).startswith('550'):
                    raise
                # If the directory is inaccessible, MKD/CWD fails rather than
                # treating an unknown remote state as permission to overwrite.
                self.ftp.mkd(part)
                self.ftp.cwd(part)

    def _parent(self, relative):
        path = PurePosixPath(relative)
        self.ftp.cwd(self.root)
        self._mkdirs(str(path.parent))
        return path.name

    def exists(self, relative):
        name = self._parent(relative)
        names = {PurePosixPath(item).name for item in self.ftp.nlst()}
        return name in names

    def write_from(self, relative, source):
        name = self._parent(relative)
        token = uuid4().hex
        staged = f'.kja-stage-{token}'
        previous = f'.kja-previous-{token}'
        moved_old = False
        installed = False
        try:
            self.ftp.storbinary('STOR ' + staged, source)
            if self.exists(relative):
                self.ftp.rename(name, previous)
                moved_old = True
            self.ftp.rename(staged, name)
            installed = True
        except BaseException:
            if moved_old and not installed:
                self.ftp.rename(previous, name)
            raise
        finally:
            if not installed:
                try:
                    self.ftp.delete(staged)
                except Exception:
                    pass
        if moved_old:
            self.ftp.delete(previous)
