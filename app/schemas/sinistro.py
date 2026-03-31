from pydantic import BaseModel
from typing import List, Optional 

class SinistroRequest(BaseModel):
    cliente_id: int
    tipo_sinistro: str
    documento_url: str

class SinistroResponse(BaseModel):
    sinistro_id: int
    status: str
    detalhes: str
    raciocinio: Optional[List[str]] = None 
    