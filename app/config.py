from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    max_upload_bytes: int = 50 * 1024 * 1024
    max_archive_bytes: int = 50 * 1024 * 1024
    max_archive_members: int = 100
    max_features: int = 100_000

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)


settings = Settings()
