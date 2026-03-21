import os
import pytesseract
from PIL import Image
import spacy
import requests
from io import BytesIO
from datetime import datetime
from dateutil.parser import parse as parse_date

from app.core.config import settings
from app.schemas.sinistro import SinistroRequest, SinistroResponse



if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    print("Modelo 'pt_core_news_sm' não encontrado. A fazer download...")
    os.system("python -m spacy download pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")
    print("Download do modelo concluído.")




def processar_sinistro_logica_IA(sinistro: SinistroRequest) -> SinistroResponse:
    print(f" Agente Analista a iniciar para cliente ID: {sinistro.cliente_id}...")
    raciocinio = []

    try:
       
        
        raciocinio.append("Passo 1: A obter e validar o documento.")
        if sinistro.documento_url.startswith('http'):
            response = requests.get(sinistro.documento_url)
            response.raise_for_status()
            imagem = Image.open(BytesIO(response.content))
        else:
            imagem = Image.open(sinistro.documento_url)
        raciocinio.append("Sucesso: Documento carregado.")

      
        
        raciocinio.append("Passo 2: A executar OCR para extrair texto.")
        texto_extraido = pytesseract.image_to_string(imagem, lang='por')
        
        if not texto_extraido or len(texto_extraido.strip()) < 20: 
            raciocinio.append("Falha no OCR: Imagem ilegível.")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Recusado", detalhes="Imagem ilegível. Envie uma foto com melhor qualidade.", raciocinio=raciocinio)
        
        raciocinio.append(f"Sucesso: Texto extraído. (Tamanho: {len(texto_extraido)} caracteres)")

       
        
        raciocinio.append("Passo 3: A executar PLN para análise de conteúdo.")
        doc = nlp(texto_extraido)

        keywords_sangue = ["sangue", "transfusão", "hemoterapia", "dador"]
        keywords_acidente = ["acidente", "trauma", "fratura", "lesão"]
        keywords_internamento = ["internado", "internamento", "baixa médica"]

        tem_sangue = any(token.lemma_.lower() in keywords_sangue for token in doc)
        tem_acidente = any(token.lemma_.lower() in keywords_acidente for token in doc)
        tem_internamento = any(token.lemma_.lower() in keywords_internamento for token in doc)
        
        raciocinio.append(f"Análise de Keywords: [Sangue: {tem_sangue}, Acidente: {tem_acidente}, Internamento: {tem_internamento}]")
        
        
        pessoas = list(set([ent.text.strip() for ent in doc.ents if ent.label_ == "PER"]))
        orgs = list(set([ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]))
        datas_str = list(set([ent.text.strip() for ent in doc.ents if ent.label_ == "DATE"]))
        
        raciocinio.append(f"Entidades Encontradas: [Pessoas: {pessoas}, Organizações: {orgs}, Datas: {datas_str}]")

       
        raciocinio.append("Passo 4: A aplicar o motor de regras avançado.")
        
       
        if datas_str:
            data_valida = False
            for data_texto in datas_str:
                try:
                    data_doc = parse_date(data_texto, dayfirst=True, fuzzy=True).date()
                    dias_passados = (datetime.now().date() - data_doc).days
                    raciocinio.append(f"Validação de Data: Encontrada '{data_texto}', com {dias_passados} dias de emissão.")
                    if dias_passados > 90:
                        raciocinio.append("Decisão: Documento muito antigo. A escalar para análise de fraude.")
                        return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Escalado para Análise Humana", detalhes="Documento com data superior a 90 dias.", raciocinio=raciocinio)
                except (ValueError, TypeError):
                    continue
        
      
        if tem_sangue and tem_acidente:
            raciocinio.append("Decisão: Ambiguidade detetada. A escalar.")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Escalado para Análise Humana", detalhes="Documento ambíguo (menciona sangue e acidente).", raciocinio=raciocinio)
            
       
        if tem_sangue and "transfusao" in sinistro.tipo_sinistro:
            raciocinio.append("Decisão: Regras para 'Amigo Sangue' cumpridas. A aprovar.")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Aprovado", detalhes="Pagamento processado para emergência de transfusão.", raciocinio=raciocinio)
        
        elif tem_acidente and tem_internamento and "acidente" in sinistro.tipo_sinistro:
            raciocinio.append("Decisão: Regras para 'Proteção Taxista' cumpridas. A aprovar.")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Aprovado", detalhes="Pagamento processado para cobertura de acidente com internamento.", raciocinio=raciocinio)
        
        else:
            raciocinio.append("Decisão: Nenhuma regra de aprovação automática foi cumprida. A escalar.")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Escalado para Análise Humana", detalhes="O documento não corresponde às regras de automação.", raciocinio=raciocinio)

    except Exception as e:
        raciocinio.append(f"Falha Crítica: {e}")
        return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Erro", detalhes=f"Erro interno do sistema: {e}", raciocinio=raciocinio)