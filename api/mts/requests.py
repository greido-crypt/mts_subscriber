import base64
import json
import random
import secrets
import string
import time
from datetime import datetime
from urllib.parse import parse_qs, urlencode

from aiohttp import ClientSession

from api.default import BaseRequest
from .models import MyTariffsList, TariffList, ActivationResponse, InviteModel, AuthModel


class MtsAPI(BaseRequest):
    def __init__(self, session: ClientSession, ya_token: str = None, base_url='https://music.mts.ru/ya_payclick'):
        headers = {
                    "Accept-API-Version": "resource=4.0, protocol=1.0",
                    "Accept": "*/*",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua": "Not/A)Brand;v=8, Chromium;v=126, Google Chrome;v=126",
                    "Sec-Fetch-Site": "same-origin",
                    "Connection": "keep-alive",
                    "sec-ch-ua-platform": "Windows",
                    "Sec-Fetch-Dest": "empty",
                    "Origin": "https://login.mts.ru",
                    "Sec-Fetch-Mode": "cors",
                    "Content-Type": "application/json"
                }

        if ya_token:
            headers['Authorization'] = f'OAuth {ya_token}'

        super().__init__(base_url=base_url, session=session, headers=headers)

    async def get_tariff_now(self, phone_number: str) -> MyTariffsList:
        self.base_url = 'https://music.mts.ru/ya_payclick'
        params = {"msisdn": phone_number}
        response = await self._get(endpoint='subscriptions', params=params)
        return MyTariffsList.model_validate_json(response.text)

    async def get_tariff_list(self, phone_number: str) -> TariffList:
        self.base_url = 'https://music.mts.ru/ya_payclick'
        params = {"msisdn": phone_number}
        response = await self._get(endpoint='content-provider/available-subscriptions', params=params)
        return TariffList.model_validate_json(response.text)

    async def activate_mts_premium(self, phone_number: str, content_id: str) -> ActivationResponse:
        self.base_url = 'https://music.mts.ru/ya_payclick'
        uid = self._generate_uid()
        bid = self._generate_bid()
        json_data = {
            "userId": f"00000000100090099{uid}",
            "bindingId": f"88b32A591b86Dbcaa98b{bid}",
            "msisdn": phone_number,
            "contentId": content_id
        }
        response = await self._post(endpoint='subscriptions', json=json_data)
        try:
            return ActivationResponse.model_validate_json(response.text)
        except Exception as e:
            return ActivationResponse(subscriptionId=None)

    async def mts_premium_auth_first_step(self, auth_data: AuthModel):
        response = await self._post_amserver_wsso_authenticate(state=auth_data.state)
        data = json.loads(response.text)

        response = await self._post_amserver_wsso_authenticate_with_data(state=auth_data.state, data=data)
        data = json.loads(response.text)

        data['callbacks'][0]['input'][0]['value'] = auth_data.phone_number
        data['callbacks'][1]['input'][0]['value'] = 1
        response = await self._post_amserver_wsso_authenticate_with_data(state=auth_data.state, data=data)

        return response

    async def mts_premium_auth_second_step(self, auth_data: AuthModel, data: dict):
        self.base_url = 'https://login.mts.ru'
        try:
            del self.headers['Authorization']
        except KeyError:
            pass
        data['callbacks'][0]['input'][0]['value'] = auth_data.sms_code
        data['callbacks'][1]['input'][0]['value'] = 1
        response = await self._post_amserver_wsso_authenticate_with_data(state=auth_data.state, data=data)
        return response

    async def _post_amserver_wsso_authenticate(self, state: str):
        self.base_url = 'https://login.mts.ru'
        params = {
            "realm": "/users",
            "client_id": "MTS_Premium",
            "authIndexType": "service",
            "authIndexValue": "login-spa",
            "goto": f"https://login.mts.ru/amserver/oauth2/authorize?client_id=MTS_Premium&redirect_uri=https%3A%2F%2Fpremium.mts.ru%2Fapi%2Fuser%2Fv1%2Fsso%2Fcallback&response_type=code&scope=account%20sub%20openid%20profile%20phone%20sso%20slaves%3Aall%20slaves%3Aprofile&service=login&state={state}",
            "statetrace": state
        }

        response = await self._post(endpoint='amserver/wsso/authenticate', params=params)
        return response

    async def _post_amserver_wsso_authenticate_with_data(self, state: str, data: dict):
        self.base_url = 'https://login.mts.ru'
        params = {
            "realm": "/users",
            "client_id": "MTS_Premium",
            "authIndexType": "service",
            "authIndexValue": "login-spa",
            "goto": f"https://login.mts.ru/amserver/oauth2/authorize?client_id=MTS_Premium&redirect_uri=https%3A%2F%2Fpremium.mts.ru%2Fapi%2Fuser%2Fv1%2Fsso%2Fcallback&response_type=code&scope=account%20sub%20openid%20profile%20phone%20sso%20slaves%3Aall%20slaves%3Aprofile&service=login&state={state}",
            "statetrace": state
        }

        response = await self._post(endpoint='amserver/wsso/authenticate', params=params, json=data)
        return response

    async def premium_authorize(self):
        try:
            del self.headers['Authorization']
        except KeyError:
            pass
        return await self._premium_sso_login()

    async def _premium_sso_login(self):
        try:
            del self.headers['Authorization']
        except KeyError:
            pass
        self.base_url = 'https://premium.mts.ru'
        response = await self._get(endpoint='api/user/v1/sso/login')
        return response

    async def mts_music_authorize(self, state: str) -> str:
        self.base_url = 'https://login.mts.ru'
        params = {
            'scope': 'ssom profile phone account sso sub openid',
            'redirect_uri': 'https://music.mts.ru/login',
            'state': state,
            'client_id': 'MTS_Music',
            'theme': 'dark',
            'response_type': 'code',
            'device_id': 'eyJpcCI6IiIsImxvY2FsZSI6InJ1IiwibW9kZWwiOiJBU1VTX0kwMDVEQSIsIm5hbWUiOiJEVUstQUwyMCIsInN5c3RlbVZlcnNpb24iOiJBbmRyb2lkIDkiLCJwbGF0Zm9ybSI6IkFuZHJvaWQiLCJzY3JlZW5TaXplIjoid2lkdGg6IDcyMCwgaGVpZ2h0OiAxMjgwIiwidGltZXpvbmUiOiJBc2lhL1NoYW5naGFpIiwidXNlcmFnZW50IjoiRGFsdmlrLzIuMS4wIChMaW51eDsgVTsgQW5kcm9pZCA5OyBBU1VTX0kwMDVEQSBCdWlsZC9QSSkiLCJ1dWlkIjoiNjE1MmMwZDMtNjMzNC00ZjZmLWI5OWYtOGU3NzgwOTI4YjBhIiwidmVuZG9yIjoiQXN1cyIsInZlcnNpb24iOiI1LjMuMCJ9'
        }

        response = await self._get(endpoint='amserver/oauth2/authorize', params=params, allow_redirects=False)
        location = response.response.headers.get('location')

        decoded_params = parse_qs(location)
        data = {
            'code': decoded_params['code'][0],
            'client_id': 'MTS_Music',
            'client_secret': 'QhpWcEO3KyPCCucXZUGgW8HfIm53DEfEa4sYx7ZPKgs4b2bv1Za3A6aE88JFQ8PO',
            'redirect_uri': 'https://music.mts.ru/login',
            'grant_type': 'authorization_code'
        }
        urlencoded_data = urlencode(data)

        response = await self._post(endpoint='amserver/oauth2/access_token', data=urlencoded_data)
        response_json = json.loads(response.text)
        access_token = response_json['access_token']
        json_data = {"version": "1", "access_token": access_token}
        base64_encoded_access_token = base64.b64encode(json.dumps(json_data).encode()).decode()

        self.base_url = 'https://mobileproxy.passport.yandex.net'
        data = {
            'provider': 'mt',
            'application': 'MTS_Music',
            'provider_token': base64_encoded_access_token
        }
        urlencoded_data = urlencode(data)

        response = await self._post(endpoint='1/bundle/auth/social/register_by_token/', data=urlencoded_data)
        response_json = json.loads(response.text)
        self.headers['Authorization'] = f"OAuth {response_json['access_token']}"
        return response_json['access_token']

    @staticmethod
    def _generate_uid():
        return ''.join(random.choice(string.digits) for _ in range(3))

    @staticmethod
    def _generate_bid():
        return ''.join(random.choice(string.hexdigits) for _ in range(12))

    async def user_invite(self, phone_number: str):
        self.base_url = 'https://premium.mts.ru'
        self.headers = {
            "Host": "premium.mts.ru",
            "Connection": "keep-alive",
            "Content-Length": "0",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": "https://premium.mts.ru",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://premium.mts.ru/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        try:
            del self.headers['Authorization']
        except KeyError:
            pass
        response = await self._post(endpoint=f'api/user/v1/invites/{phone_number}')
        return InviteModel.Model.model_validate_json(response.text)

    async def delete_all_subscriptions(self):
        self.base_url = 'https://premium.mts.ru'
        try:
            del self.headers['Authorization']
        except KeyError:
            pass
        response = await self._delete(endpoint='api/mhsrv/v1/subscriptions/all')
        return response

    def export_cookies(self, skip_ip_cookies=False):
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

            if cookie.key in ['qrator_ssid', 'qrator_jsid', 'qrator_jsr'] and skip_ip_cookies:
                continue

            cookies_list.append({
                'name': cookie.key,
                'value': cookie.value,
                'domain': f".{cookie.get('domain', '')}" if cookie.get('domain', '') else "",
                'path': cookie.get('path', ''),
                'httponly': bool(cookie.get('httponly', True)),
                'hostOnly': bool(cookie.get('hostOnly', False)),
                'secure': bool(cookie.get('secure', False)),
                'expirationDate': expirationDate,
                'sameSite': cookie.get('sameSite', None) if cookie.get('sameSite', '') else None,
                'storeId': cookie.get('storeId', None) if cookie.get('storeId', '') else None,
                'session': bool(cookie.get('session', True))
            })

        return json.dumps(cookies_list)

    @staticmethod
    def generate_random_string(length=128):
        characters = string.ascii_letters + string.digits + "+/"
        return ''.join(secrets.choice(characters) for _ in range(length))

    def import_cookies(self, cookies_list: list[dict]):
        self.headers['Cookie'] = '; '.join(f"{cookie['name']}={cookie['value']}" for cookie in cookies_list)
