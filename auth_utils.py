# auth_utils.py
import os
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from urllib.request import urlopen
import json

# --- CONFIGURAÇÃO DO AUTH0 (PREENCHIDA PARA VOCÊ!) ---
# Estes valores vêm do seu painel Auth0
AUTH0_DOMAIN = "dev-cqu7d0oryo1uoi7c.us.auth0.com"  # O seu "Domain"
API_IDENTIFIER = "https://api.segurafacil.com"      # O seu "Identifier"
ALGORITHMS = ["RS256"]

# --- Lógica de Validação (Receita Padrão) ---
# Não precisa de se preocupar em decorar este código,
# ele é uma implementação padrão para verificar tokens RS256.

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def get_token_auth_header(token: str = Depends(oauth2_scheme)):
    return token

def verify_token(token: str = Depends(oauth2_scheme)):
    jsonurl = urlopen(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Unable to parse authentication token.")
    
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_IDENTIFIER,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token is expired.")
        except jwt.JWTClaimsError:
            raise HTTPException(status_code=401, detail="Incorrect claims, please check the audience and issuer.")
        except Exception:
            raise HTTPException(status_code=401, detail="Unable to parse authentication token.")
            
    raise HTTPException(status_code=401, detail="Unable to find appropriate key.")