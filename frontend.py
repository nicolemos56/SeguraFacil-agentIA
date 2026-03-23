import streamlit as st
import requests
from PIL import Image


try:
    API_URL = st.secrets["API_URL"]
except:
    st.error("URL da API não configurado nos segredos do Streamlit.")
    st.stop()



st.set_page_config(page_title="SeguraFácil", page_icon="")
st.title("SeguraFácil - Processamento de Sinistros com IA")
st.markdown(
    "Bem-vindo à demonstração do Agente de IA da SeguraFácil. "
    "Esta interface permite-lhe submeter um pedido de sinistro para análise automática."
)

st.subheader("1. Autenticação")
st.info(
    "Para interagir com a nossa API segura, por favor, insira um Access Token válido obtido no painel "
    "de teste da sua API no Auth0.",
    icon=""
)
access_token = st.text_input("Auth0 Access Token", type="password")

st.subheader("2. Detalhes do Sinistro")

with st.form("sinistro_form"):
    st.write("Por favor, preencha os dados abaixo e anexe o documento comprovativo.")
    
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
    
    submitted = st.form_submit_button("Analisar Sinistro com Agente IA")

if submitted:
    if not access_token:
        st.error("Erro: O Access Token do Auth0 é obrigatório.")
    elif uploaded_file is None:
        st.error("Erro: Por favor, anexe um documento para análise.")
    else:
        with st.spinner("O Agente de IA está a analisar o documento... "):
            try:
              
                headers = {"Authorization": f"Bearer {access_token}"}
                
              
                data = {
                    "cliente_id": cliente_id,
                    "tipo_sinistro": tipo_sinistro,
                }
                
              
                files = {
                    "uploaded_document": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                }

             
                response = requests.post(API_URL, headers=headers, data=data, files=files)

              
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

                    if 'raciocinio' in resultado and resultado['raciocinio']:
                        with st.expander("Ver o Raciocínio do Agente de IA "):
                            for passo in resultado['raciocinio']:
                                st.text(f"-> {passo}")
                
                elif response.status_code == 401:
                    st.error("Falha na Autenticação! O seu Access Token é inválido ou expirou.")
                else:
                    st.error(f"Ocorreu um erro na API: {response.status_code} - {response.text}")
            
            except Exception as e:
                st.error(f"Ocorreu um erro crítico na aplicação frontend: {e}")