# frontend.py
import streamlit as st
import requests
import os
from PIL import Image

# --- CONFIGURAÇÕES DA APLICAÇÃO ---
# O endereço da sua API FastAPI.
# Se estiver a executar tudo na mesma máquina, este é o endereço padrão.
API_URL = "http://127.0.0.1:8000/api/agente/processar-sinistro"
TEMP_DIR = "temp_docs" # Pasta para guardar temporariamente os uploads

# Criar a pasta temporária se ela não existir
os.makedirs(TEMP_DIR, exist_ok=True)

# --- INTERFACE DA APLICAÇÃO ---

# 1. Título e Descrição
st.set_page_config(page_title="SeguraFácil", page_icon="🛡️")
st.title("🛡️ SeguraFácil - Processamento de Sinistros com IA")
st.markdown(
    "Bem-vindo à demonstração do Agente de IA da SeguraFácil. "
    "Esta interface permite-lhe submeter um pedido de sinistro para análise automática."
)

# 2. Autenticação (Input do Token)
st.subheader("1. Autenticação")
st.info(
    "Para interagir com a nossa API segura, por favor, insira um Access Token válido "
    "obtido no painel de teste da sua API no Auth0.",
    icon="🔑"
)
access_token = st.text_input("Auth0 Access Token", type="password")

# 3. Formulário de Submissão de Sinistro
st.subheader("2. Detalhes do Sinistro")

with st.form("sinistro_form"):
    st.write("Por favor, preencha os dados abaixo e anexe o documento comprovativo.")
    
    # Inputs do formulário
    cliente_id = st.number_input("ID do Cliente", min_value=1, value=1001, step=1)
    
    tipo_sinistro = st.selectbox(
        "Tipo de Sinistro",
        ("emergencia_transfusao_sangue", "acidente_pessoal_taxista"),
        index=0
    )
    
    uploaded_file = st.file_uploader(
        "Anexe o documento (Atestado Médico, Requisição, etc.)",
        type=["png", "jpg", "jpeg"]
    )
    
    # Botão de submissão do formulário
    submitted = st.form_submit_button("Analisar Sinistro com Agente IA")

# 4. Lógica de Processamento Após Submissão
if submitted:
    # Validações iniciais
    if not access_token:
        st.error("Erro: O Access Token do Auth0 é obrigatório.")
    elif uploaded_file is None:
        st.error("Erro: Por favor, anexe um documento para análise.")
    else:
        # Mostrar um spinner de carregamento enquanto o agente trabalha
        with st.spinner("O Agente de IA está a analisar o documento... 🤖"):
            try:
                # Salvar o ficheiro temporariamente para que a API possa acedê-lo
                file_path = os.path.join(TEMP_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Montar o pedido para a API
                headers = {"Authorization": f"Bearer {access_token}"}
                payload = {
                    "cliente_id": cliente_id,
                    "tipo_sinistro": tipo_sinistro,
                    "documento_url": file_path  # A API vai ler este caminho local
                }

                # Chamar a nossa API backend
                response = requests.post(API_URL, headers=headers, json=payload)

                # Processar a resposta da API
                if response.status_code == 200:
                    st.success("Análise concluída com sucesso!")
                    resultado = response.json()
                    
                    st.subheader("Resultado da Análise do Agente:")
                    if resultado['status'] == 'Aprovado':
                        st.balloons()
                        st.success(f"**Status:** {resultado['status']}")
                    elif resultado['status'] == 'Recusado':
                        st.error(f"**Status:** {resultado['status']}")
                    else:
                        st.warning(f"**Status:** {resultado['status']}")
                    
                    st.write(f"**Detalhes:** {resultado['detalhes']}")

                elif response.status_code == 401:
                    st.error("Falha na Autenticação! O seu Access Token é inválido ou expirou.")
                else:
                    st.error(f"Ocorreu um erro na API: {response.status_code} - {response.text}")
            
            except Exception as e:
                st.error(f"Ocorreu um erro crítico na aplicação frontend: {e}")