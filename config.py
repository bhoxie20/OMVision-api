from pydantic_settings import BaseSettings, SettingsConfigDict
import os

IS_LAMBDA = os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str

    api_key: str

    harmonic_api_key: str

    class Config:
        env_file = ".env"


settings = Settings()
