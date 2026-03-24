from typing import Optional, Union
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str

class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Optional[str]


class RefreshTokenSchemas(BaseModel):
    refresh_token: Union[str, None]
