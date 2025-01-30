import json

import aiohttp
from smsactivate.api import SMSActivateAPI

from api.default import BaseRequest, BaseRequestModel
from api.sms_activate.models import GetBalance, GetStatus, GetNumberV2, GetNumber


class SmsActivate(BaseRequest):
    def __init__(self, session: aiohttp.ClientSession, api_key: str,
                 base_url: str = 'https://api.sms-activate.org/stubs/handler_api.php'):

        self.api_key = api_key

        self.__CODES = {
            'STATUS_WAIT_CODE': 'Waiting for sms',
            'STATUS_WAIT_RETRY': 'Past Inappropriate Code - Waiting for Code Refinement',
            'STATUS_WAIT_RESEND': 'Waiting for re-sending SMS',
            'STATUS_CANCEL': 'Activation canceled',
            'STATUS_OK': 'Code received',
            'FULL_SMS': 'Full text received'
        }

        self.__RENT_CODES = {
            'STATUS_WAIT_CODE': 'Waiting for the first SMS',
            'STATUS_FINISH': 'Rent paid and completed',
            'STATUS_CANCEL': 'Rent canceled with a refund',
        }

        self.__ERRORS = {
            'NO_NUMBERS': 'There are no free numbers for receiving SMS from the current service',
            'NO_BALANCE': 'Not enough funds',
            'BAD_ACTION': 'Invalid action (action parameter)',
            'BAD_SERVICE': 'Incorrect service name (service parameter)',
            'BAD_KEY': 'Invalid API access key',
            'ERROR_SQL': 'One of the parameters has an invalid value.',
            'SQL_ERROR': 'One of the parameters has an invalid value.',
            'NO_ACTIVATION': 'The specified activation id does not exist',
            'BAD_STATUS': 'Attempt to establish a non-existent status',
            'STATUS_CANCEL': 'Current activation canceled and no longer available',
            'BANNED': 'Account is blocked',
            'NO_CONNECTION': 'No connection to servers sms-activate',
            'ACCOUNT_INACTIVE': 'No numbers available',
            'NO_ID_RENT': 'Rent id not specified',
            'INVALID_PHONE': 'The number was not rented by you (wrong rental id)',
            'STATUS_FINISH': 'Rent paid and completed',
            'INCORECT_STATUS': 'Missing or incorrect status',
            'CANT_CANCEL': 'Unable to cancel the lease (more than 20 minutes have passed)',
            'ALREADY_FINISH': 'The lease has already been completed',
            'ALREADY_CANCEL': 'The lease has already been canceled',
            'WRONG_OPERATOR': 'Lease Transfer Operator is not MTT',
            'NO_YULA_MAIL': 'To buy a number from the mail group holding, you must have at least 500 rubles on your account',
            'WHATSAPP_NOT_AVAILABLE': 'No WhatsApp numbers available',

            'NOT_INCOMING': 'Activation is not call-verified activation',
            'INVALID_ACTIVATION_ID': 'Invalid activation id',

            'WRONG_ADDITIONAL_SERVICE': 'Invalid additional service (only services for forwarding are allowed)',
            'WRONG_ACTIVATION_ID': 'Invalid parental activation ID',
            'WRONG_SECURITY': 'An error occurred when trying to transfer an activation ID without forwarding, or a completed / inactive activation',
            'REPEAT_ADDITIONAL_SERVICE': 'The error occurs when you try to order the purchased service again',

            'NO_KEY': 'API key missing',
            'OPERATORS_NOT_FOUND': 'Operators not found'
        }

        super().__init__(base_url=base_url, session=session)

    def _check_errors(self, action: str, response: BaseRequestModel):
        response_status = response.text.split(':')[0]
        if self.__ERRORS.get(response_status):
            raise Exception(response_status, self.__ERRORS.get(response_status), action)

    async def getNumbersStatus(self, country: int, operator: str):
        """Запрос количества доступных номеров"""
        params = {'api_key': self.api_key,
                  'action': 'getNumbersStatus',
                  'country': country,
                  'operator': operator}
        response = await self._get(params=params)
        self._check_errors(action=params.get('action'), response=response)
        return response

    async def getTopCountriesByService(self, service: str = None, freePrice: bool = False):
        """Запрос топ стран по сервису FreePrice"""
        params = {
            'api_key': self.api_key,
            'action': 'getTopCountriesByService'
        }
        if service:
            params['service'] = service
        if freePrice:
            params['freePrice'] = 'true'

        response = await self._get(params=params)
        self._check_errors(action=params.get('action'), response=response)

        return response

    async def getBalance(self):
        """Запрос баланса"""
        params = {
            'api_key': self.api_key,
            'action': 'getBalance'
        }
        response = await self._get(params=params)
        self._check_errors(action=params.get('action'), response=response)
        json_data = json.dumps({"balance": response.text.split(':')[-1]})
        return GetBalance.model_validate_json(json_data)

    async def getBalanceAndCashBack(self):
        """Запрос баланса с кэшбэк-счетом"""
        params = {
            'api_key': self.api_key,
            'action': 'getBalanceAndCashBack'
        }
        response = await self._get(params=params)
        self._check_errors(action=params.get('action'), response=response)

        return response

    async def getOperators(self, country: int = None):
        """Запрос доступных операторов"""
        params = {
            'api_key': self.api_key,
            'action': 'getOperators'
        }
        if country:
            params['country'] = country

        response = await self._get(params=params)
        self._check_errors(action=params.get('action'), response=response)

        return response

    async def getActiveActivations(self):
        """Запрос активных активаций"""
        params = {
            'api_key': self.api_key,
            'action': 'getActiveActivations'
        }
        response = await self._get(params=params)
        self._check_errors(action=params.get('action'), response=response)

        return response

    async def getNumber(self, service: str, country: int, forward: int = 0, maxPrice: int = None,
                        phoneException: str = None, operator: str = None, verification: bool = False,
                        ref: str = None, useCashBack: bool = False):
        """Запрос номера FreePrice"""
        params = {
            'api_key': self.api_key,
            'action': 'getNumber',
            'service': service,
            'country': country,
            'forward': forward,
        }
        if maxPrice is not None:
            params['maxPrice'] = maxPrice
        if phoneException:
            params['phoneException'] = phoneException
        if operator:
            params['operator'] = operator
        if verification:
            params['verification'] = 'true'
        if ref:
            params['ref'] = ref
        if useCashBack:
            params['useCashBack'] = 'true'

        response = await self._get(params=params)
        self._check_errors(action=params.get('action'), response=response)
        response_data = response.text.split(':')
        return GetNumber(status=response_data[0], activationId=response_data[1], phoneNumber=response_data[2])

    async def getNumberV2(self, service: str, country: int, forward: int = 0, maxPrice: int = None,
                          phoneException: str = None, operator: str = None, verification: bool = False,
                          ref: str = None):
        """Запрос номера V2 FreePrice"""
        params = {
            'api_key': self.api_key,
            'action': 'getNumberV2',
            'service': service,
            'country': country,
            'forward': forward,
        }

        if maxPrice is not None:
            params['maxPrice'] = maxPrice
        if phoneException:
            params['phoneException'] = phoneException
        if operator:
            params['operator'] = operator
        if verification:
            params['verification'] = 'true'
        if ref:
            params['ref'] = ref

        response = await self._get(params=params)
        self._check_errors(action=params.get('action'), response=response)

        return GetNumberV2.model_validate_json(response.text)

    async def setStatus(self, id: int, status: int, forward: str = None):
        """Изменение статуса активации"""
        params = {
            'api_key': self.api_key,
            'action': 'setStatus',
            'id': id,
            'status': status,
        }
        if forward:
            params['forward'] = forward

        response = await self._get(params=params)
        self._check_errors(action=params.get('action'), response=response)

        return response

    async def getStatus(self, id: int):
        """Получить состояние активации"""
        params = {
            'api_key': self.api_key,
            'action': 'getStatus',
            'id': id
        }
        response = await self._get(params=params)
        self._check_errors(action=params.get('action'), response=response)
        response_list = response.text.split(':')

        if len(response_list) == 2:
            json_data = {"status": response_list[0], 'sms_code': response_list[1]}
        else:
            json_data = {"status": response_list[0], 'sms_code': None}

        json_data = json.dumps(json_data)

        return GetStatus.model_validate_json(json_data=json_data)
