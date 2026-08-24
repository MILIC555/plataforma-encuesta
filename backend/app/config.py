# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost:3306/encuestas_db"
    OPENAI_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    HF_MODEL_SENTIMENT: str = "pysentimiento/robertuito-sentiment-analysis"
    HF_MODEL_TOPIC: str = "Recognai/bert-base-spanish-wwm-cased-xnli"
    SECRET_KEY: str = "cambiar-en-produccion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 horas

    class Config:
        env_file = ".env"


settings = Settings()
