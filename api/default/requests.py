import asyncio
import json
import re
import time
from datetime import datetime
from http.cookies import BaseCookie, SimpleCookie
from urllib.parse import urlencode

import aiohttp
from yarl import URL

from .models import BaseRequestModel


class CustomCookie(SimpleCookie):
    def value_encode(self, val):
        return str(val), val


class BaseRequest:
    def __init__(self,
                 session: aiohttp.ClientSession,
                 base_url: str,
                 headers: dict = None,
                 proxy: str = None,
                 debug: bool = True,
                 timeout: int = 10):
        self.base_url = base_url
        self.headers = headers or {}
        self.proxy = proxy
        self.timeout = timeout
        self.debug = debug
        self.session = session

    async def _make_request(self, method: str, endpoint: str = None, **kwargs) -> BaseRequestModel:
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        headers = self.headers.copy()

        if 'json' in kwargs:
            json_data = kwargs.pop('json')
            kwargs['data'] = json.dumps(json_data, separators=(',', ':'))
            headers['Content-Type'] = "application/json; charset=utf-8"

        elif 'data' in kwargs:
            headers['Content-Type'] = "application/x-www-form-urlencoded"

        if 'params' in kwargs:
            params = kwargs.pop('params')
            url = f"{url}?{urlencode(params)}"

        if self.debug:
            dict_kwargs = {**kwargs}
            print(f'[DEBUG] Request URL: {url} Params: {dict_kwargs} Headers: {headers}')

        try:
            async with self.session.request(method=method, url=url, headers=headers,
                                            proxy=self.proxy, timeout=self.timeout, **kwargs) as response:
                response_text = await response.text()
                if self.debug:
                    print(f'[DEBUG] Response URL: {url} Status: {response.status} Response: {response_text}')

                return BaseRequestModel(text=response_text, status_code=response.status, response=response)
        except (aiohttp.ClientHttpProxyError, asyncio.TimeoutError) as e:
            if self.debug:
                print(f'[ERROR] Request failed: {e}. Retrying...')
            return await self._make_request(method, endpoint, **kwargs)

    async def _get(self, endpoint: str = None, **kwargs) -> BaseRequestModel:
        return await self._make_request(method="GET", endpoint=endpoint, **kwargs)

    async def _post(self, endpoint: str = None, **kwargs) -> BaseRequestModel:
        return await self._make_request(method="POST", endpoint=endpoint, **kwargs)

    async def _put(self, endpoint: str = None, **kwargs) -> BaseRequestModel:
        return await self._make_request(method="PUT", endpoint=endpoint, **kwargs)

    async def _delete(self, endpoint: str = None, **kwargs) -> BaseRequestModel:
        return await self._make_request(method="DELETE", endpoint=endpoint, **kwargs)

    def export_cookies(self):
        cookies_list = []
        for cookie in self.session.cookie_jar:
            expires = cookie.get('expires', '')
            expirationDate = None
            if expires:
                try:
                    expires_time = datetime.strptime(expires, '%a, %d-%b-%Y %H:%M:%S %Z')
                    expirationDate = time.mktime(expires_time.timetuple())
                except ValueError:
                    pass

            cookies_list.append({
                'name': cookie.key,
                'value': cookie.value,
                'domain': f".{cookie.get('domain', '')}" if cookie.get('domain', '') else "",
                'path': cookie.get('path', ''),
                'httponly': bool(cookie.get('httponly', True)),  # Default to True
                'hostOnly': bool(cookie.get('hostOnly', False)),
                'secure': bool(cookie.get('secure', False)),
                'expirationDate': expirationDate,
                'sameSite': cookie.get('sameSite', None) if cookie.get('sameSite', '') else None,
                'storeId': cookie.get('storeId', None) if cookie.get('storeId', '') else None,
                'session': bool(cookie.get('session', True))  # Default to True
            })
        return json.dumps(cookies_list)

    def clean_cookie_value(self, value: str) -> str:
        # Удаляем все ненужные символы переноса строки и другие нежелательные символы
        return re.sub(r'[\r\n\t]', '', value).strip()

    def import_cookies(self, cookies_list: list[dict]):
        for cookie in cookies_list:
            cookie_name = str(cookie['name'])
            # Remove any extraneous quotes and clean the value
            cookie_value = self.clean_cookie_value(str(cookie['value']).strip('"'))
            domain = cookie.get('domain', '')

            # Debugging output to verify cookie values
            if self.debug:
                print(f"[DEBUG] Importing cookie: {cookie_name}={cookie_value}")
                print(f"[DEBUG] Cookie domain: {domain}")

            # Add cookie using SimpleCookie
            cookie_obj = CustomCookie()
            cookie_obj[cookie_name] = cookie_value
            cookie_obj[cookie_name]['domain'] = domain
            cookie_obj[cookie_name]['path'] = cookie.get('path', '/')
            if 'expires' in cookie:
                cookie_obj[cookie_name]['expires'] = cookie['expires']
            if 'httponly' in cookie:
                cookie_obj[cookie_name]['httponly'] = cookie['httponly']
            if 'secure' in cookie:
                cookie_obj[cookie_name]['secure'] = cookie['secure']
            if 'samesite' in cookie:
                cookie_obj[cookie_name]['samesite'] = cookie['samesite']

            # Add cookie to session
            for key, morsel in cookie_obj.items():
                self.session.cookie_jar.update_cookies({key: morsel.value}, response_url=URL(f"https://{domain}"))

    def clear_cookies(self):
        self.session.cookie_jar.clear()
