# app/auth/utils.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from urllib.request import urlopen
import json
from app.core.config import settings # <-- Importa as configurações

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# (O resto do seu código de verify_token, mas substitua as variáveis
# hardcoded pelas do objeto 'settings')

def verify_token(token: str = Depends(oauth2_scheme)):
    jsonurl = urlopen(f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json")
    # ... e assim por diante
    # payload = jwt.decode(..., audience=settings.API_IDENTIFIER, ...)