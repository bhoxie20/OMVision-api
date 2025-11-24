from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from config import settings

api_key_header = APIKeyHeader(name="X-API-Key")


def get_current_user(api_key: str = Security(api_key_header)):

    if api_key == settings.api_key:
        return True

    raise HTTPException(status_code=403, detail="Unauthorized")
