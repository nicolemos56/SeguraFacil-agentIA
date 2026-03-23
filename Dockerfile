# 1. Começar com uma imagem base oficial do Python
FROM python:3.9-slim

# 2. Definir o diretório de trabalho dentro do contentor
WORKDIR /code

# 3. Instalar as dependências do sistema
RUN apt-get update && apt-get install -y \
    # A "Caixa de Ferramentas" para compilar código
    build-essential \
    # Dependências para a biblioteca 'lxml' (muito comum)
    libxml2-dev libxslt-dev \
    # A nossa dependência principal para OCR
    tesseract-ocr tesseract-ocr-por \
    # Limpar o cache para manter a imagem pequena
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar o arquivo de requisitos e instalar as bibliotecas Python
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5. Garante que o modelo do spaCy seja baixado durante o build
RUN python -m spacy download pt_core_news_sm

# 6. Copiar todo o código da nossa aplicação para dentro do contentor
COPY ./app /code/app

# 7. Expor a porta que o Uvicorn vai usar
EXPOSE 8000

# 8. O comando para iniciar a nossa API quando o contentor arrancar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]