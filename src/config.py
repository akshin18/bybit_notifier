from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    ADMIN_IDS: list[int] = []
    DB_URL: str = "sqlite://db.sqlite3"
    API_ID: int = 0
    API_HASH: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
