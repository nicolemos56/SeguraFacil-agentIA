# Dockerfile (VERSÃO FINAL)

# 1. Começar com uma imagem base oficial e leve do Python
FROM python:3.9-slim

# 2. Definir o diretório de trabalho dentro do contentor
WORKDIR /code

# 3. Instalar as dependências do sistema operativo (Tesseract + Idioma Português)
# Esta é a etapa crucial que falha num deploy normal sem Docker.
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar e instalar as dependências Python
# Copiamos o requirements.txt primeiro para aproveitar o cache do Docker
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5. Fazer o download do modelo de linguagem do spaCy durante o build
# Isto garante que o modelo já estará presente quando a aplicação iniciar.
RUN python -m spacy download pt_core_news_sm

# 6. Copiar todo o código da nossa aplicação para dentro do contentor
COPY ./app /code/app

# 7. Expor a porta que o Uvicorn vai usar
EXPOSE 8000

# 8. O comando para iniciar a nossa API quando o contentor arrancar
# O host 0.0.0.0 é essencial para ser acessível de fora do contentor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]