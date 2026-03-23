# app/main.py

# 1. IMPORTS: Adicionamos UploadFile, File e Form do FastAPI
from fastapi import FastAPI, Depends, UploadFile, File, Form
from app.auth.utils import verify_token
from app.schemas.sinistro import SinistroRequest, SinistroResponse
from app.services.agente_ia import processar_sinistro_logica_IA

app = FastAPI(
    title="SeguraFácil AgentIA",
    description="API do Agente de IA para processamento de sinistros de micro-seguro."
)

# --- ESTES ENDPOINTS NÃO MUDAM ---
@app.get("/api/public")
def public_endpoint():
    return {"message": "Este endpoint é público."}

@app.get("/api/private")
def private_endpoint(payload: dict = Depends(verify_token)):
    return {"message": "Este endpoint é privado.", "user_info": payload}

# --- ESTE ENDPOINT FOI TOTALMENTE MODIFICADO ---
@app.post("/api/agente/processar-sinistro", response_model=SinistroResponse, tags=["Agente IA"])
def endpoint_processar_sinistro(
    # 2. ASSINATURA DA FUNÇÃO: Agora recebemos os dados como campos de formulário e um ficheiro,
    # em vez de um único JSON.
    cliente_id: int = Form(...),
    tipo_sinistro: str = Form(...),
    uploaded_document: UploadFile = File(...),
    payload: dict = Depends(verify_token)
):
    """
    Processa um novo pedido de sinistro recebendo o documento diretamente via upload.
    """
    # 3. LÓGICA INTERNA: Nós reconstruímos o objeto SinistroRequest manualmente
    # para passar para a nossa camada de serviço.
    # O ponto crucial é passar 'uploaded_document.file', que é o objeto do ficheiro em memória.
    sinistro_request = SinistroRequest(
        cliente_id=cliente_id,
        tipo_sinistro=tipo_sinistro,
        documento_url=uploaded_document.file 
    )
    
    # A chamada ao nosso serviço de IA continua exatamente igual
    decisao = processar_sinistro_logica_IA(sinistro_request)
    return decisaox