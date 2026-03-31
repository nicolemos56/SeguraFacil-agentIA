from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # AUTH0
    AUTH0_DOMAIN: str
    AUTH0_CLIENT_ID: str
    AGENT_CLIENT_ID: str
    AGENT_CLIENT_SECRET: str
    API_IDENTIFIER: str

    # PAYPAL
    PAYPAL_CLIENT_ID: str
    PAYPAL_SECRET: str

    # SISTEMA
    TESSERACT_CMD: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()