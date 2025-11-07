from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Grape Finance"
    mongodb_url: str = "mongodb://localhost:27017/grape_finance"
    
    class Config:
        env_file = ".env"

settings = Settings()
