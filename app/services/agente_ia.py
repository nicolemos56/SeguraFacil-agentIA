# app/services/agente_ia.py
import os

from app.schemas.sinistro import SinistroRequest, SinistroResponse
from app.core.config import settings
import pytesseract
from PIL import Image
import spacy
import requests # Para fazer download da imagem a partir de um URL
from io import BytesIO

# --- Configurações Iniciais ---
# Configurar o caminho do Tesseract (se estiver a usar Windows)
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

# Carregar o modelo de PLN do spaCy (isto pode ser lento na primeira vez)
try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    print("Modelo 'pt_core_news_sm' não encontrado. A executar 'python -m spacy download pt_core_news_sm'")
    os.system("python -m spacy download pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")


def processar_sinistro_logica(sinistro: SinistroRequest) -> SinistroResponse:
    """
    Versão com IA que usa OCR e PLN para analisar um documento.
    """
    print(f"🤖 Agente de IA a iniciar análise para o cliente ID: {sinistro.cliente_id}...")
    
    try:
        # --- Passo 1: Obter a Imagem ---
        # Vamos assumir que documento_url pode ser um URL ou um caminho local
        if sinistro.documento_url.startswith('http'):
            response = requests.get(sinistro.documento_url)
            response.raise_for_status() # Lança um erro se o download falhar
            imagem = Image.open(BytesIO(response.content))
        else:
            imagem = Image.open(sinistro.documento_url) # Abre um caminho local

        # --- Passo 2: OCR - Extrair texto da imagem ---
        texto_extraido = pytesseract.image_to_string(imagem, lang='por')
        print(f"   [OCR] Texto extraído (primeiros 200 chars): \n---\n{texto_extraido[:200].strip()}...\n---")

        if not texto_extraido.strip():
            return SinistroResponse(sinistro_id=0, status="Recusado", detalhes="Não foi possível ler o texto do documento.")

        # --- Passo 3: PLN - Analisar o texto ---
        doc = nlp(texto_extraido)
        for ent in doc.ents:
            print(f"   [PLN-Entidade] Texto: '{ent.text}', Tipo: '{ent.label_}'")

        keywords_sangue = ["sangue", "transfusão", "hemoterapia", "dador"]
        keywords_acidente = ["acidente", "trauma", "fratura", "queda", "colisão"]
        keywords_internamento = ["internado", "internamento", "baixa médica"]

        tem_sangue = any(token.lemma_.lower() in keywords_sangue for token in doc)
        tem_acidente = any(token.lemma_.lower() in keywords_acidente for token in doc)
        tem_internamento = any(token.lemma_.lower() in keywords_internamento for token in doc)
        
        print(f"   [PLN] Análise: Sangue? {tem_sangue}, Acidente? {tem_acidente}, Internamento? {tem_internamento}")

        # --- Passo 4: Motor de Decisão ---
        if tem_sangue and "transfusao" in sinistro.tipo_sinistro:
            print("   [Decisão] Gatilho 'Amigo Sangue' ativado.")
            return SinistroResponse(sinistro_id=123, status="Aprovado", detalhes="Pagamento processado para emergência de transfusão.")
        
        elif tem_acidente and tem_internamento and "acidente" in sinistro.tipo_sinistro:
            print("   [Decisão] Gatilho 'Proteção Taxista' ativado.")
            return SinistroResponse(sinistro_id=124, status="Aprovado", detalhes="Pagamento processado para cobertura de acidente com internamento.")
        
        else:
            print("   [Decisão] Regras não cumpridas. A escalar para análise humana.")
            return SinistroResponse(sinistro_id=125, status="Escalado para Análise Humana", detalhes="O conteúdo do documento não corresponde às regras de aprovação automática.")

    except FileNotFoundError:
        print(f"   [Erro] Ficheiro não encontrado: {sinistro.documento_url}")
        return SinistroResponse(sinistro_id=0, status="Erro", detalhes="O ficheiro do documento não foi encontrado.")
    except Exception as e:
        print(f"   [Erro] Ocorreu um erro inesperado: {e}")
        return SinistroResponse(sinistro_id=0, status="Erro", detalhes=f"Erro interno do sistema: {e}")