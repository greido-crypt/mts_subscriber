from typing import Optional

from pydantic import BaseModel


class GetNumber(BaseModel):
    status: str
    activationId: str
    phoneNumber: str


class GetNumberV2(BaseModel):
    activationId: str
    phoneNumber: str
    activationCost: str
    countryCode: str
    canGetAnotherSms: bool
    activationTime: str
    activationEndTime: str
    activationOperator: str


class GetBalance(BaseModel):
    balance: float


class GetStatus(BaseModel):
    status: str
    sms_code: Optional[str] = None


