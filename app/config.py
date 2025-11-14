from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    GEMINI_API_KEY: str
    HF_SPACE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = ".env"

settings = Settings()