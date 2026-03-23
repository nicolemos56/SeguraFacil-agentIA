# app/services/agente_ia.py (VERSÃO FINAL E CORRIGIDA PARA UPLOAD DIRETO)

import os
import pytesseract
from PIL import Image
import spacy
from datetime import datetime
from dateutil.parser import parse as parse_date

from app.core.config import settings
from app.schemas.sinistro import SinistroRequest, SinistroResponse

# --- CONFIGURAÇÕES INICIAIS E CARREGAMENTO DE MODELOS ---

# Configurar o caminho do Tesseract APENAS se estiver a usar Windows.
# No Docker (Linux), o Tesseract já está no "PATH" do sistema.
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

# Carregar o modelo de PLN do spaCy.
# O Dockerfile garante que este modelo já foi baixado no ambiente de produção.
# A lógica try/except é um fallback útil para o desenvolvimento local.
try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    print("Modelo 'pt_core_news_sm' não encontrado. A fazer download...")
    os.system("python -m spacy download pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")


# --- SERVIÇO PRINCIPAL DO AGENTE DE IA ---

def processar_sinistro_logica_IA(sinistro: SinistroRequest) -> SinistroResponse:
    """
    Processa um pedido de sinistro usando um pipeline de OCR, PLN e um motor de regras.
    Esta versão recebe o ficheiro da imagem diretamente em memória.
    """
    print(f"🤖 Agente Analista a iniciar para cliente ID: {sinistro.cliente_id}...")
    raciocinio = []

    try:
        # ### ALTERAÇÃO PRINCIPAL AQUI ###
        # Passo 1: Obter e Validar o Documento (diretamente do objeto de ficheiro)
        raciocinio.append("Passo 1: A carregar documento recebido em memória.")
        # A função Image.open() consegue ler diretamente do objeto de ficheiro
        # que o FastAPI nos dá. A lógica de http vs local foi removida.
        imagem = Image.open(sinistro.documento_url)
        raciocinio.append("Sucesso: Documento carregado.")

        # Passo 2: OCR - Extração de Texto
        raciocinio.append("Passo 2: A executar OCR para extrair texto.")
        texto_extraido = pytesseract.image_to_string(imagem, lang='por')
        
        if not texto_extraido or len(texto_extraido.strip()) < 20: 
            raciocinio.append("Falha no OCR: Imagem ilegível ou com pouco texto.")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Recusado", detalhes="Imagem ilegível. Por favor, envie uma foto com melhor qualidade e iluminação.", raciocinio=raciocinio)
        
        raciocinio.append(f"Sucesso: Texto extraído. (Tamanho: {len(texto_extraido)} caracteres)")

        # Passo 3: PLN - Análise de Conteúdo (Nenhuma alteração necessária aqui)
        raciocinio.append("Passo 3: A executar PLN para análise de conteúdo.")
        doc = nlp(texto_extraido)

        # Análise de Keywords
        keywords_sangue = ["sangue", "transfusão", "hemoterapia", "dador"]
        keywords_acidente = ["acidente", "trauma", "fratura", "lesão", "colisão"]
        keywords_internamento = ["internado", "internamento", "baixa médica"]
        tem_sangue = any(token.lemma_.lower() in keywords_sangue for token in doc)
        tem_acidente = any(token.lemma_.lower() in keywords_acidente for token in doc)
        tem_internamento = any(token.lemma_.lower() in keywords_internamento for token in doc)
        raciocinio.append(f"Análise de Keywords: [Sangue: {tem_sangue}, Acidente: {tem_acidente}, Internamento: {tem_internamento}]")
        
        # Extração de Entidades Nomeadas (NER)
        pessoas = list(set([ent.text.strip() for ent in doc.ents if ent.label_ == "PER"]))
        orgs = list(set([ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]))
        datas_str = list(set([ent.text.strip() for ent in doc.ents if ent.label_ == "DATE"]))
        raciocinio.append(f"Entidades Encontradas: [Pessoas: {len(pessoas)}, Organizações: {len(orgs)}, Datas: {len(datas_str)}]")

        # Passo 4: Motor de Decisão com Regras de "Pensamento de Produção" (Nenhuma alteração necessária aqui)
        raciocinio.append("Passo 4: A aplicar o motor de regras avançado.")
        
        # Regra de Validação de Datas (caso extremo)
        if datas_str:
            for data_texto in datas_str:
                try:
                    data_doc = parse_date(data_texto, dayfirst=True, fuzzy=True).date()
                    dias_passados = (datetime.now().date() - data_doc).days
                    raciocinio.append(f"Validação de Data: Encontrada '{data_texto}', com {dias_passados} dias de emissão.")
                    if dias_passados < 0 or dias_passados > 90:
                        raciocinio.append("Decisão: Documento com data inválida (futura ou > 90 dias). A escalar.")
                        return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Escalado para Análise Humana", detalhes="Documento com data de emissão inválida.", raciocinio=raciocinio)
                except (ValueError, TypeError):
                    continue
        
        # Regra de Ambiguidade (caso extremo)
        if tem_sangue and tem_acidente:
            raciocinio.append("Decisão: Ambiguidade detetada (menciona sangue e acidente). A escalar.")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Escalado para Análise Humana", detalhes="Documento ambíguo, requer revisão humana.", raciocinio=raciocinio)
            
        # Regras de Aprovação Automática
        if tem_sangue and "transfusao" in sinistro.tipo_sinistro:
            raciocinio.append("Decisão: Regras para 'Amigo Sangue' cumpridas. A aprovar.")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Aprovado", detalhes="Pagamento processado para emergência de transfusão.", raciocinio=raciocinio)
        
        elif tem_acidente and tem_internamento and "acidente" in sinistro.tipo_sinistro:
            raciocinio.append("Decisão: Regras para 'Proteção Taxista' cumpridas. A aprovar.")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Aprovado", detalhes="Pagamento processado para cobertura de acidente com internamento.", raciocinio=raciocinio)
        
        else:
            raciocinio.append("Decisão: Nenhuma regra de aprovação automática foi cumprida. A escalar.")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Escalado para Análise Humana", detalhes="O documento não corresponde às regras de automação.", raciocinio=raciocinio)

    # Tratamento de erros, incluindo o erro de não conseguir abrir a imagem
    except Exception as e:
        raciocinio.append(f"Falha Crítica: {e}")
        return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Erro", detalhes=f"Erro interno do sistema: {e}", raciocinio=raciocinio)