from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    FIREBASE_CRED_PATH: str
    FIREBASE_DB_URL: str
    MONGO_URI: str
    DB_NAME: str

    class Config:
        env_file = ".env"
        extra = "forbid"  # or "ignore" if you want to allow extras


settings = Settings()
