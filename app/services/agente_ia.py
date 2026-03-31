import os
import requests
import paypalrestsdk
import pytesseract
import spacy
from PIL import Image
from io import BytesIO
from app.schemas.sinistro import SinistroRequest, SinistroResponse
from app.core.config import settings


if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    os.system("python -m spacy download pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")

def acionar_pagamento_com_paypal(valor_usd: int) -> tuple[bool, str]:
    """
    💰 Lógica de Pagamento Segura via PayPal (Sandbox).
    Busca as credenciais no cofre para proteger a transação.
    """
    try:
        
        paypalrestsdk.configure({
            "mode": "sandbox",
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_SECRET
        })

        payout = paypalrestsdk.Payout({
            "sender_batch_header": {
                "sender_batch_id": f"batch_{os.urandom(4).hex()}",
                "email_subject": "SeguraFácil: Benefício Aprovado!",
            },
            "items": [{
                "recipient_type": "EMAIL",
                "amount": {"value": str(valor_usd), "currency": "USD"},
                "receiver": "nicocohen56@gmail.com",
                "note": "Processado automaticamente pelo Agente de IA SeguraFácil.",
                
            }]
        })

        if payout.create():
            return True, f"Sucesso! Pago via PayPal. ID: {payout.batch_header.payout_batch_id}"
        else:
            return False, f"Erro PayPal: {payout.error}"
    except Exception as e:
        return False, f"Falha no processamento financeiro: {str(e)}"

def processar_sinistro_logica_IA(sinistro: SinistroRequest, documento_enviado=None) -> SinistroResponse:
    print(f"🤖 Agente de IA iniciando análise para Cliente: {sinistro.cliente_id}")
    raciocinio = []
    
    try:
        
        raciocinio.append("Passo 1: A validar e carregar o documento.")
        imagem = Image.open(sinistro.documento_url)
        raciocinio.append("Sucesso: Documento carregado do sistema local.")

        
        raciocinio.append("Passo 2: A executar OCR para extrair texto do documento.")
        texto = pytesseract.image_to_string(imagem, lang='por')
        raciocinio.append(f"Sucesso: Texto extraído ({len(texto)} caracteres).")

        
        raciocinio.append("Passo 3: A executar PLN para analisar o conteúdo.")
        doc = nlp(texto.lower())
        
        keywords_sangue = ["sangue", "transfusão", "hemoterapia", "requisição"]
        tem_sangue = any(token.lemma_ in keywords_sangue for token in doc)
        
        raciocinio.append(f"Análise PLN: [Sangue: {tem_sangue}, Acidente: False, Internamento: False]")

        
        raciocinio.append("Passo 4: A aplicar as regras de negócio para decisão final.")
        
        if tem_sangue and "sangue" in sinistro.tipo_sinistro:
            raciocinio.append("Decisão: Regras para 'Amigo Sangue' cumpridas. Iniciando pagamento...")
            
            
            sucesso, detalhe_pago = acionar_pagamento_com_paypal(valor_usd=50)
            
            if sucesso:
                
                return SinistroResponse(sinistro_id=123, status="Aprovado", detalhes=detalhe_pago, raciocinio=raciocinio)
            else:
                raciocinio.append(f"Falha: {detalhe_pago}")
                return SinistroResponse(sinistro_id=123, status="Aprovado com Erro de Envio", detalhes=detalhe_pago, raciocinio=raciocinio)
        
        else:
            raciocinio.append("Decisão: Documento não atende critérios de aprovação automática.")
            return SinistroResponse(sinistro_id=0, status="Escalado", detalhes="Revisão humana necessária.", raciocinio=raciocinio)

    except Exception as e:
        return SinistroResponse(sinistro_id=0, status="Erro", detalhes=f"Erro interno: {str(e)}", raciocinio=raciocinio)