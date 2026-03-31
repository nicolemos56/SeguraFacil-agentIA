from fastapi import FastAPI, HTTPException
from app.schemas.sinistro import SinistroRequest, SinistroResponse
from app.services.agente_ia import processar_sinistro_logica_IA, acionar_pagamento_com_paypal

app = FastAPI(title="SeguraFácil - Orquestrador Financeiro")


BASE_DADOS_SINISTROS = {}

@app.post("/api/agente/submeter-sinistro")
def submeter(sinistro: SinistroRequest):
    
    resultado = processar_sinistro_logica_IA(sinistro)
    
    claim_id = len(BASE_DADOS_SINISTROS) + 1
    
    
    BASE_DADOS_SINISTROS[claim_id] = {
        "id": claim_id,
        "cliente": sinistro.cliente_id,
        "status": resultado.status, 
        "detalhes": resultado.detalhes,
        "raciocinio": resultado.raciocinio, 
        "payout_id": None
    }
    return {"id": claim_id, **resultado.model_dump()}


@app.get("/api/oficial/pendentes")
def listar_pendentes():
    return [v for k, v in BASE_DADOS_SINISTROS.items() if v['payout_id'] is None]
    resultado = processar_sinistro_logica_IA(sinistro)
    claim_id = len(BASE_DADOS_SINISTROS) + 1
    
    
    BASE_DADOS_SINISTROS[claim_id] = {
        "id": claim_id,
        "cliente": sinistro.cliente_id,
        "status": "Aguardando Oficial" if resultado.status == "Aprovado" else "Revisão Manual",
        "detalhes": resultado.detalhes,
        "payout_id": None
    }
    return {"id": claim_id, **resultado.model_dump()}

@app.get("/api/sinistros/{claim_id}")
def status_sinistro(claim_id: int):
    if claim_id not in BASE_DADOS_SINISTROS:
        raise HTTPException(status_code=404, detail="Não encontrado")
    return BASE_DADOS_SINISTROS[claim_id]

@app.get("/api/oficial/pendentes")
def listar_pendentes():
    return [v for k, v in BASE_DADOS_SINISTROS.items() if v['status'] == "Aguardando Oficial"]

@app.post("/api/oficial/autorizar/{claim_id}")
def autorizar(claim_id: int):
    sucesso, msg = acionar_pagamento_com_paypal(valor_usd=50)
    if sucesso:
        BASE_DADOS_SINISTROS[claim_id]["status"] = "Pago"
        BASE_DADOS_SINISTROS[claim_id]["payout_id"] = msg.split("ID: ")[-1]
        return {"message": "Sucesso", "payout_id": BASE_DADOS_SINISTROS[claim_id]["payout_id"]}
    raise HTTPException(status_code=500, detail=msg)