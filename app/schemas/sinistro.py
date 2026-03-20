# app/schemas/sinistro.py
from pydantic import BaseModel

class SinistroRequest(BaseModel):
    cliente_id: int
    tipo_sinistro: str
    documento_url: str

class SinistroResponse(BaseModel):
    sinistro_id: int
    status: str
    detalhes: str