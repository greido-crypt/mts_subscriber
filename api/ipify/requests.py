import aiohttp

from api.default import BaseRequest
from .models import IPAddress


class IpifyAPI(BaseRequest):
    def __init__(self, session: aiohttp.ClientSession, base_url: str = 'https://api.ipify.org'):
        super().__init__(session, base_url)

    async def get_ip(self):
        response = await self._get(endpoint='')
        return IPAddress(ip_address=response.text)
