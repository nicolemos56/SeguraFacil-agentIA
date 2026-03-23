from fastapi import FastAPI, Depends, UploadFile, File, Form
from app.auth.utils import verify_token
from app.schemas.sinistro import SinistroRequest, SinistroResponse
from app.services.agente_ia import processar_sinistro_logica

app = FastAPI(
    title="SeguraFácil AgentIA",
    description="API do Agente de IA para processamento de sinistros de micro-seguro."
)

@app.get("/api/public")
def public_endpoint():
    return {"message": "Este endpoint é público."}

@app.get("/api/private")
def private_endpoint(payload: dict = Depends(verify_token)):
    return {"message": "Este endpoint é privado.", "user_info": payload}

@app.post("/api/agente/processar-sinistro", response_model=SinistroResponse, tags=["Agente IA"])
def endpoint_processar_sinistro(
   
    cliente_id: int = Form(...),
    tipo_sinistro: str = Form(...),
    uploaded_document: UploadFile = File(...),
    payload: dict = Depends(verify_token)
):
    """
    Processa um novo pedido de sinistro recebendo o documento diretamente.
    """
   
    sinistro_request = SinistroRequest(
        cliente_id=cliente_id,
        tipo_sinistro=tipo_sinistro,
        documento_url=uploaded_document.file 
    )
    
    decisao = processar_sinistro_logica(sinistro_request)
    return decisao