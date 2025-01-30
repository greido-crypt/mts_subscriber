from pydantic import BaseModel


class IPAddress(BaseModel):
    ip_address: str