from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    APP_NAME: str = "DefaultAppName"

    # Off unless a deployment asks for it. Debug mode serves tracebacks and
    # internal state to whoever made the request, so the unconfigured default
    # is the safe one rather than the convenient one.
    DEBUG: bool = False

    # No default: a deployment that forgets to set this should fail loudly
    # rather than sign tokens with a publicly known key.
    JWT_SECRET: str

    DATABASE_URL: str
    DATABASE_ISOLATION_LEVEL: str = "REPEATABLE READ"

    MESSAGE_BROKER_URL: str
    MESSAGE_BROKER_TYPE: str = "rabbit"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Every required setting is read from the environment or the .env file.
config = AppConfig()  # type: ignore[call-arg]
