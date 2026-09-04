from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    APP_NAME: str = "DefaultAppName"

    # Serves tracebacks and internal state to the caller, so off by default.
    DEBUG: bool = False

    # No default: a deployment that forgets this should fail loudly rather
    # than sign tokens with a publicly known key.
    JWT_SECRET: str

    DATABASE_URL: str
    DATABASE_ISOLATION_LEVEL: str = "REPEATABLE READ"

    MESSAGE_BROKER_URL: str
    MESSAGE_BROKER_TYPE: str = "rabbit"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = AppConfig()  # type: ignore[call-arg]
