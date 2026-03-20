# app/core/config.py
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    AUTH0_DOMAIN: str
    API_IDENTIFIER: str
    ALGORITHMS: list = ["RS256"]
    
    # Adicione esta linha (substitua pelo seu caminho)
    TESSERACT_CMD: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    class Config:
        env_file = ".env"

settings = Settings()