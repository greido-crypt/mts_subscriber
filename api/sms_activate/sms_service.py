import asyncio
import time

from api.sms_activate.requests import SmsActivate


class SmsActivateService(SmsActivate):
    async def get_sms_code(self, id: int | str, delay: float = 5, time_out: float = 5):
        """
        :param delay: delay in seconds
        :param id: number id
        :param time_out: timeout in minutes
        :return:
        """
        start_time = time.time()
        while start_time + time_out * 60 > time.time():
            phone_status = await self.getStatus(id=id)
            if phone_status.sms_code:
                return phone_status
            await asyncio.sleep(delay)
        else:
            raise TimeoutError('Timeout while getting sms code for id {}'.format(id))