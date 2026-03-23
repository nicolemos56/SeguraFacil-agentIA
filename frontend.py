import streamlit as st
import requests
import os
from PIL import Image

# --- CONFIGURAÇÕES DA APLICAÇÃO ---
# O URL da API é carregado a partir dos "Secrets" do Streamlit.
try:
    API_URL = st.secrets["API_URL"]
except FileNotFoundError:
    # Fallback para desenvolvimento local se os secrets não existirem
    API_URL = "http://127.0.0.1:8000/api/agente/processar-sinistro"

# --- INTERFACE DA APLICAÇÃO ---

# 1. Título e Descrição
st.set_page_config(page_title="SeguraFácil", page_icon="🛡️", layout="centered")

st.title("🛡️ SeguraFácil - Processamento de Sinistros com IA")
st.markdown("Bem-vindo à demonstração do Agente de IA da SeguraFácil. "
            "Esta interface permite-lhe submeter um pedido de sinistro para análise automática.")

# 2. Autenticação (Input do Token)
st.subheader("1. Autenticação")
st.info("Para interagir com a nossa API segura, por favor, insira um Access Token válido "
        "obtido no painel de teste da sua API no Auth0.", icon="🔑")
access_token = st.text_input("Auth0 Access Token", type="password", help="O seu token não será guardado.")

# 3. Formulário de Submissão de Sinistro
st.subheader("2. Detalhes do Sinistro")
with st.form("sinistro_form"):
    st.write("Por favor, preencha os dados abaixo e anexe o documento comprovativo.")
    
    col1, col2 = st.columns(2)
    with col1:
        cliente_id = st.number_input("ID do Cliente", min_value=1, value=1001, step=1)
    with col2:
        tipo_sinistro = st.selectbox(
            "Tipo de Sinistro",
            ("emergencia_transfusao_sangue", "acidente_pessoal_taxista"),
            index=0
        )
    
    uploaded_file = st.file_uploader(
        "Anexe o documento (Atestado Médico, Requisição, etc.)",
        type=["png", "jpg", "jpeg"]
    )
    
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
                # ==================== INÍCIO DAS ALTERAÇÕES ====================

                # Montar o pedido para a API como "multipart/form-data"
                headers = {
                    "Authorization": f"Bearer {access_token}"
                }
                
                # Os campos do formulário vão no 'data'
                data = {
                    "cliente_id": cliente_id,
                    "tipo_sinistro": tipo_sinistro,
                }
                
                # O ficheiro vai no 'files'
                # A chave 'uploaded_document' DEVE corresponder ao nome do parâmetro na API
                files = {
                    "uploaded_document": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                }

                # Chamar a nossa API backend com os novos parâmetros
                # Trocamos 'json=payload' por 'data=data' e 'files=files'
                response = requests.post(API_URL, headers=headers, data=data, files=files)
               
                # ===================== FIM DAS ALTERAÇÕES ======================

                # O restante do código para processar a resposta permanece o mesmo
                if response.status_code == 200:
                    st.success("Análise concluída com sucesso!")
                    resultado = response.json()
                    
                    st.subheader("Resultado da Análise do Agente:")
                    
                    status = resultado.get('status', 'N/A')
                    if status == 'Aprovado':
                        st.balloons()
                        st.success(f"**Status:** {status}")
                    elif status == 'Recusado':
                        st.error(f"**Status:** {status}")
                    else:
                        st.warning(f"**Status:** {status}")
                    
                    st.write(f"**Detalhes:** {resultado.get('detalhes', 'Nenhum detalhe fornecido.')}")

                    if 'raciocinio' in resultado and resultado.get('raciocinio'):
                        with st.expander("Ver o Raciocínio do Agente de IA 🧠"):
                            for passo in resultado['raciocinio']:
                                st.text(f"-> {passo}")

                elif response.status_code == 401:
                    st.error("Falha na Autenticação! O seu Access Token é inválido ou expirou.")
                else:
                    st.error(f"Ocorreu um erro na API: {response.status_code} - {response.text}")
            
            except Exception as e:
                st.error(f"Ocorreu um erro crítico na aplicação frontend: {e}")