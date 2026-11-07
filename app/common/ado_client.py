from dataclasses import dataclass, field
import os
from urllib.parse import quote, urlsplit
import httpx


@dataclass(frozen=True)
class AdoConfig:
    base_url: str
    project: str
    pat: str = field(repr=False)
    api_version: str = '7.1'

    @classmethod
    def from_env(cls):
        values = [os.getenv(name, '').strip() for name in ('ADO_BASE_URL', 'ADO_PROJECT', 'ADO_PAT')]
        if not all(values):
            raise ValueError('ADO_BASE_URL, ADO_PROJECT, ADO_PAT 환경변수가 필요합니다.')
        parsed = urlsplit(values[0])
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc or parsed.username or parsed.query or parsed.fragment:
            raise ValueError('ADO_BASE_URL must be an HTTP(S) organization/collection URL')
        return cls(*values, api_version=os.getenv('ADO_API_VERSION', '7.1'))


class AdoClient:
    """Shared async REST client. Supports Azure DevOps and Server collection URLs."""
    def __init__(self, config=None, *, transport=None):
        self.config = config or AdoConfig.from_env()
        self._client = httpx.AsyncClient(
            base_url=f'{self.config.base_url.rstrip("/")}/{quote(self.config.project, safe="")}/_apis/',
            auth=httpx.BasicAuth('', self.config.pat), timeout=30,
            transport=transport, follow_redirects=False,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self._client.aclose()

    async def request(self, method, path, **kwargs):
        if path.startswith('/') or '..' in path or '://' in path:
            raise ValueError('Use a relative API path')
        params = dict(kwargs.pop('params', {}) or {})
        params.setdefault('api-version', self.config.api_version)
        try:
            response = await self._client.request(method, path, params=params, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f'ADO 요청 실패 (HTTP {exc.response.status_code})') from None
        except httpx.RequestError:
            raise RuntimeError('ADO 서버에 연결할 수 없습니다. URL과 네트워크를 확인하세요.') from None

    async def query_wiql(self, query):
        return await self.request('POST', 'wit/wiql', json={'query': query})

    async def get_work_items(self, ids):
        items = []
        for start in range(0, len(ids), 200):
            result = await self.request('POST', 'wit/workitemsbatch', json={'ids': ids[start:start + 200]})
            items.extend(result.get('value', []))
        return items

    async def list_repositories(self):
        return await self.request('GET', 'git/repositories')

    async def compare_commits(self, repository, base, target):
        return await self.request('GET', f'git/repositories/{quote(repository, safe="")}/diffs/commits', params={
            'baseVersion': base, 'baseVersionType': 'commit',
            'targetVersion': target, 'targetVersionType': 'commit',
        })
