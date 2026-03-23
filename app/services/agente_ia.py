# app/services/agente_ia.py

from app.schemas.sinistro import SinistroRequest, SinistroResponse
from app.core.config import settings
import pytesseract
from PIL import Image
import spacy
import os

# --- Configurações Iniciais ---
# Configurar o caminho do Tesseract APENAS se estiver a usar Windows
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

# Carregar o modelo de PLN do spaCy
nlp = spacy.load("pt_core_news_sm")


def processar_sinistro_logica(sinistro: SinistroRequest) -> SinistroResponse:
    """
    Versão com IA que usa OCR e PLN para analisar um documento.
    """
    print(f"🤖 Agente de IA a iniciar análise para o cliente ID: {sinistro.cliente_id}...")
    raciocinio = []
    
    try:
        raciocinio.append("Passo 1: A obter e validar o documento.")
        
        ### ALTERAÇÃO PRINCIPAL AQUI ###
        # A lógica foi simplificada. Image.open() agora recebe diretamente
        # o objeto de ficheiro que veio da API, sem precisar de verificar se é URL ou caminho.
        imagem = Image.open(sinistro.documento_url)
        raciocinio.append("Sucesso: Documento carregado e aberto como imagem.")

        # --- O resto do código continua exatamente o mesmo ---
        
        raciocinio.append("Passo 2: A executar OCR para extrair texto do documento.")
        texto_extraido = pytesseract.image_to_string(imagem, lang='por')

        if not texto_extraido or len(texto_extraido.strip()) < 20:
            raciocinio.append("Falha no OCR: Não foi possível extrair texto legível da imagem.")
            return SinistroResponse(sinistro_id=0, status="Recusado", detalhes="Imagem ilegível. Por favor, envie uma foto com melhor qualidade e iluminação.", raciocinio=raciocinio)
        
        raciocinio.append(f"Sucesso: Texto extraído. (Tamanho: {len(texto_extraido)} caracteres)")

        raciocinio.append("Passo 3: A executar PLN para analisar o conteúdo.")
        doc = nlp(texto_extraido)

        keywords_sangue = ["sangue", "transfusão", "hemoterapia", "dador"]
        keywords_acidente = ["acidente", "trauma", "fratura", "queda", "colisão"]
        keywords_internamento = ["internado", "internamento", "baixa médica"]

        tem_sangue = any(token.lemma_.lower() in keywords_sangue for token in doc)
        tem_acidente = any(token.lemma_.lower() in keywords_acidente for token in doc)
        tem_internamento = any(token.lemma_.lower() in keywords_internamento for token in doc)
        
        raciocinio.append(f"Análise PLN: [Sangue: {tem_sangue}, Acidente: {tem_acidente}, Internamento: {tem_internamento}]")

        raciocinio.append("Passo 4: A aplicar o motor de regras para decisão.")
        
        if tem_sangue and tem_acidente:
            raciocinio.append("Decisão: Ambiguidade detetada (menciona sangue e acidente). A escalar para análise humana para evitar erro.")
            return SinistroResponse(sinistro_id=125, status="Escalado para Análise Humana", detalhes="Documento ambíguo. Um agente humano irá rever o caso.", raciocinio=raciocinio)
            
        if tem_sangue and "transfusao" in sinistro.tipo_sinistro:
            raciocinio.append("Decisão: Regras para 'Amigo Sangue' cumpridas. A aprovar.")
            return SinistroResponse(sinistro_id=123, status="Aprovado", detalhes="Pagamento processado para emergência de transfusão.", raciocinio=raciocinio)
        
        elif tem_acidente and tem_internamento and "acidente" in sinistro.tipo_sinistro:
            raciocinio.append("Decisão: Regras para 'Proteção Taxista' cumpridas. A aprovar.")
            return SinistroResponse(sinistro_id=124, status="Aprovado", detalhes="Pagamento processado para cobertura de acidente com internamento.", raciocinio=raciocinio)
        
        else:
            raciocinio.append("Decisão: Nenhuma regra de aprovação automática foi cumprida. A escalar.")
            return SinistroResponse(sinistro_id=125, status="Escalado para Análise Humana", detalhes="O conteúdo do documento não corresponde às regras de aprovação automática.", raciocinio=raciocinio)

    except Exception as e:
        raciocinio.append(f"Falha Crítica: {e}")
        return SinistroResponse(sinistro_id=0, status="Erro", detalhes=f"Erro interno do sistema: {e}", raciocinio=raciocinio)