# 1. Começar com uma imagem base oficial do Python
FROM python:3.9-slim

# 2. Definir o diretório de trabalho dentro do contentor
WORKDIR /code

# 3. Instalar as dependências do sistema (AQUI ESTÁ A MAGIA)
# Instala o Tesseract e o pacote de idioma português
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar o arquivo de requisitos e instalar as bibliotecas Python
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5. Copiar todo o código da nossa aplicação para dentro do contentor
COPY ./app /code/app

# 6. Expor a porta que o Uvicorn vai usar
EXPOSE 8000

# 7. O comando para iniciar a nossa API quando o contentor arrancar
# O host 0.0.0.0 é crucial para ser acessível de fora do contentor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]