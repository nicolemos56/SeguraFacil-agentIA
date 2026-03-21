# app/services/agente_ia.py
import os
import pytesseract
from PIL import Image
import spacy
import requests
from io import BytesIO

# Importar as configurações e os schemas da nossa aplicação
from app.core.config import settings
from app.schemas.sinistro import SinistroRequest, SinistroResponse

# --- CONFIGURAÇÕES INICIAIS DO SERVIÇO ---

# Configurar o caminho do Tesseract (essencial para Windows)
# Esta verificação garante que o código funcione em diferentes sistemas operativos.
if os.name == 'nt': # 'nt' significa que estamos no Windows
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

# Carregar o modelo de PLN do spaCy.
# Envolvemos em try/except para garantir que o modelo seja baixado se não existir.
# Esta é uma boa prática para tornar a aplicação mais fácil de configurar.
try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    print("Modelo 'pt_core_news_sm' não encontrado. A tentar fazer o download...")
    os.system("python -m spacy download pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")
    print("Download concluído com sucesso.")

# --- LÓGICA PRINCIPAL DO AGENTE DE IA ---

def processar_sinistro_logica_IA(sinistro: SinistroRequest) -> SinistroResponse:
    """
    Processa um pedido de sinistro usando um pipeline de IA robusto (OCR e PLN).
    O agente regista os seus passos de raciocínio e lida com falhas comuns.
    """
    print(f"🤖 Agente de IA a iniciar análise para o cliente ID: {sinistro.cliente_id}...")
    
    # REFINAMENTO 1: Rastreamento do Raciocínio do Agente
    # Esta lista irá registar cada passo que o agente toma, para depuração e transparência.
    raciocinio = []

    try:
        # --- Passo 1: Obter e Validar o Documento ---
        raciocinio.append("Passo 1: A obter e validar o documento.")
        
        if sinistro.documento_url.startswith('http'):
            response = requests.get(sinistro.documento_url)
            response.raise_for_status() # Lança um erro HTTP se o download falhar
            imagem = Image.open(BytesIO(response.content))
        else: # Assumimos que é um caminho de ficheiro local
            imagem = Image.open(sinistro.documento_url)
        
        raciocinio.append("Sucesso: Documento carregado e aberto como imagem.")

        # --- Passo 2: OCR - Extrair texto da imagem ---
        raciocinio.append("Passo 2: A executar OCR para extrair texto do documento.")
        texto_extraido = pytesseract.image_to_string(imagem, lang='por') # 'por' para português
        
        # REFINAMENTO 2: Lidar com Falhas de Forma Elegante (Pensamento de Produção)
        # Se o OCR não conseguir extrair um texto minimamente útil, recusa de forma clara.
        if not texto_extraido or len(texto_extraido.strip()) < 20: 
            raciocinio.append("Falha no OCR: Não foi possível extrair texto legível da imagem.")
            print(f"   [Decisão] Recusado devido a imagem ilegível. Raciocínio: {raciocinio}")
            return SinistroResponse(
                sinistro_id=sinistro.cliente_id, 
                status="Recusado", 
                detalhes="Imagem ilegível. Por favor, envie uma foto com melhor qualidade, focada e com boa iluminação."
            )
        
        raciocinio.append(f"Sucesso: Texto extraído. (Tamanho: {len(texto_extraido)} caracteres)")
        print(f"   [OCR] Texto extraído (prévia): '{texto_extraido.strip()[:100]}...'")

        # --- Passo 3: PLN - Analisar o conteúdo do texto ---
        raciocinio.append("Passo 3: A executar PLN para analisar o conteúdo.")
        doc = nlp(texto_extraido)

        # Definir as palavras-chave para cada tipo de cobertura
        keywords_sangue = ["sangue", "transfusão", "hemoterapia", "dador"]
        keywords_acidente = ["acidente", "trauma", "fratura", "queda", "colisão", "lesão"]
        keywords_internamento = ["internado", "internamento", "baixa médica", "hospitalizado"]

        # Verificar a presença das palavras-chave
        tem_sangue = any(token.lemma_.lower() in keywords_sangue for token in doc)
        tem_acidente = any(token.lemma_.lower() in keywords_acidente for token in doc)
        tem_internamento = any(token.lemma_.lower() in keywords_internamento for token in doc)
        
        raciocinio.append(f"Análise PLN: [Sangue: {tem_sangue}, Acidente: {tem_acidente}, Internamento: {tem_internamento}]")
        print(f"   [PLN] Análise: Sangue? {tem_sangue}, Acidente? {tem_acidente}, Internamento? {tem_internamento}")

        # --- Passo 4: Motor de Decisão com Pensamento de Produção ---
        raciocinio.append("Passo 4: A aplicar o motor de regras para decisão.")
        
        # REFINAMENTO 3: Lidar com Casos Extremos e Ambiguidade
        if tem_sangue and tem_acidente:
            raciocinio.append("Decisão: Ambiguidade detetada (menciona tanto sangue como acidente). A escalar para análise humana para evitar erro.")
            print(f"   [Decisão] Escalado devido a ambiguidade. Raciocínio: {raciocinio}")
            return SinistroResponse(
                sinistro_id=sinistro.cliente_id, 
                status="Escalado para Análise Humana", 
                detalhes="Documento ambíguo. Um agente humano irá rever o caso para garantir a decisão correta."
            )
            
        # Regras de negócio claras
        if tem_sangue and "transfusao" in sinistro.tipo_sinistro:
            raciocinio.append("Decisão: Regras para 'Amigo Sangue' cumpridas. A aprovar.")
            print(f"   [Decisão] Aprovado. Raciocínio: {raciocinio}")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Aprovado", detalhes="Pagamento processado para emergência de transfusão.")
        
        elif tem_acidente and tem_internamento and "acidente" in sinistro.tipo_sinistro:
            raciocinio.append("Decisão: Regras para 'Proteção Taxista' cumpridas. A aprovar.")
            print(f"   [Decisão] Aprovado. Raciocínio: {raciocinio}")
            return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Aprovado", detalhes="Pagamento processado para cobertura de acidente com internamento.")

        else:
            raciocinio.append("Decisão: Nenhuma regra de aprovação automática foi cumprida com base no documento e no tipo de sinistro. A escalar.")
            print(f"   [Decisão] Escalado, regras não cumpridas. Raciocínio: {raciocinio}")
            return SinistroResponse(
                sinistro_id=sinistro.cliente_id, 
                status="Escalado para Análise Humana", 
                detalhes="O conteúdo do documento não corresponde às regras para aprovação automática. Um agente humano irá rever o caso."
            )

    except requests.exceptions.RequestException as e:
        raciocinio.append(f"Falha Crítica: Não foi possível fazer o download do documento do URL: {e}")
        print(f"   [ERRO] Download do documento falhou. Raciocínio: {raciocinio}")
        return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Erro", detalhes="O link para o documento parece estar inválido ou offline.")
    except FileNotFoundError:
        raciocinio.append(f"Falha Crítica: Ficheiro não encontrado no caminho local: {sinistro.documento_url}")
        print(f"   [ERRO] Ficheiro não encontrado. Raciocínio: {raciocinio}")
        return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Erro", detalhes="O ficheiro do documento não foi encontrado.")
    except Exception as e:
        raciocinio.append(f"Falha Crítica: Ocorreu um erro inesperado durante o processamento: {e}")
        print(f"   [ERRO] Erro inesperado. Raciocínio: {raciocinio}")
        return SinistroResponse(sinistro_id=sinistro.cliente_id, status="Erro", detalhes=f"Erro interno do sistema: {e}")