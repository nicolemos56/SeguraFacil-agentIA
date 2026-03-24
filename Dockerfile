# Dockerfile CORRIGIDO E FINAL

# 1. Imagem Base: Começamos com uma imagem oficial do Python 3.11
FROM python:3.11-slim

# 2. Variáveis de Ambiente: Boas práticas para o Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Instalar Dependências do Sistema (A NOSSA ALTERAÇÃO AQUI!)
# Antes de instalar qualquer coisa do Python, instalamos o Tesseract.
RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*

# 4. Definir o Diretório de Trabalho
WORKDIR /code

# 5. Copiar e Instalar as Dependências Python
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 6. Copiar o Código da Aplicação
COPY ./app /code/app

# 7. Comando para Executar a Aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]