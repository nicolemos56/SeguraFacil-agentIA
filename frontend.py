import streamlit as st
import requests
from urllib.parse import urlencode
import os
import platform
from dotenv import load_dotenv

# --- CARREGAR LÓGICA DIRETAMENTE (Estratégia para Deploy na Nuvem) ---
try:
    from app.services.agente_ia import processar_sinistro_logica_IA, acionar_pagamento_com_paypal
    from app.schemas.sinistro import SinistroRequest
except ImportError:
    st.error("🚨 Erro: Pasta 'app' não encontrada. Verifique a estrutura do projeto.")

load_dotenv()

# --- CONFIGURAÇÕES VIA .ENV ---
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8501")

# Detectar pasta temporária correta (Windows vs Linux/Cloud)
TEMP_DIR = "/tmp" if platform.system() == "Linux" else "C:/temp"
if not os.path.exists(TEMP_DIR):
    try:
        os.makedirs(TEMP_DIR)
    except:
        pass # Fallback para diretório atual se falhar no Windows

st.set_page_config(page_title="SeguraFácil AgentIA", layout="wide", page_icon="🛡️")

# --- PERSISTÊNCIA DE DADOS EM NUVEM (Fila Local caso o Backend falhe) ---
if 'fila_cloud' not in st.session_state:
    st.session_state.fila_cloud = {}

# --- NAVEGAÇÃO E REDIRECIONAMENTO ---
query_params = st.query_params
if "role" in query_params:
    st.session_state.role = query_params["role"]
if "code" in query_params and "role" not in query_params:
    # Se voltamos do Auth0 sem role na URL, assumimos Oficial (fluxo do Vault)
    st.session_state.role = 'oficial' 

# --- PÁGINA INICIAL (HOME) ---
if 'role' not in st.session_state or st.session_state.role is None:
    st.title("🛡️ Welcome to SeguraFácil")
    st.subheader("Autonomous Micro-insurance for Emerging Markets")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚖 INFORMAL WORKER PORTAL (Taxi Drivers)"):
            st.session_state.role = 'taxista'
            st.rerun()
    with col2:
        if st.button("🏢 INSURANCE OFFICER PORTAL (Management)"):
            st.session_state.role = 'oficial'
            st.rerun()

# --- PORTAL DO TAXISTA ---
elif st.session_state.role == 'taxista':
    st.sidebar.button("⬅️ Sair do Portal", on_click=lambda: st.session_state.update({"role": None}))
    st.title("🚖 Informal Worker Panel")
    
    if 'meu_sinistro_id' not in st.session_state:
        st.info("Submeta o seu comprovativo médico para receber o benefício instantâneo.")
        doc = st.file_uploader("Submeter Comprovativo (JPG/PNG)", type=['png', 'jpg', 'jpeg'])
        
        if st.button("Enviar para Análise do Agente"):
            if doc:
                with st.spinner("🤖 Agente de IA analisando documento e verificando conformidade..."):
                    temp_path = os.path.join(TEMP_DIR, doc.name)
                    with open(temp_path, "wb") as f: 
                        f.write(doc.getbuffer())
                    
                    payload = {"cliente_id": 123, "tipo_sinistro": "sangue", "documento_url": temp_path}
                    
                    try:
                        # Tenta Backend Local
                        res = requests.post(f"{API_URL}/api/agente/submeter-sinistro", json=payload, timeout=3).json()
                        st.session_state.meu_sinistro_id = res['id']
                    except:
                        # Fallback: Execução Direta (Deploy na Nuvem)
                        req_obj = SinistroRequest(cliente_id=123, tipo_sinistro="sangue", documento_url=temp_path)
                        res_ia = processar_sinistro_logica_IA(req_obj)
                        new_id = len(st.session_state.fila_cloud) + 1
                        st.session_state.fila_cloud[new_id] = {
                            "id": new_id, "cliente": 123, "status": "Aguardando Oficial", 
                            "detalhes": res_ia.detalhes, "raciocinio": res_ia.raciocinio, "payout_id": None
                        }
                        st.session_state.meu_sinistro_id = new_id
                    st.rerun()
    else:
        # CONSULTA STATUS (API ou Memória Local)
        status_res = None
        try:
            resp = requests.get(f"{API_URL}/api/sinistros/{st.session_state.meu_sinistro_id}", timeout=2)
            if resp.status_code == 200: status_res = resp.json()
        except:
            status_res = st.session_state.fila_cloud.get(st.session_state.meu_sinistro_id)

        # TRATAMENTO SEGURO DO STATUS (Evita KeyError)
        current_status = status_res.get('status') if status_res else "Processando"

        if current_status == "Pago":
            st.balloons()
            st.success("🎉 O SEU PAGAMENTO CHEGOU!")
            st.container(border=True).markdown(f"""
                ### 🧾 Recibo de Benefício
                **Status:** Pago via PayPal ✅  
                **Valor Transferido:** $50.00 USD  
                **ID Transação:** `{status_res.get('payout_id', 'N/A')}`
            """)
            if st.button("Submeter Novo Sinistro"): 
                del st.session_state.meu_sinistro_id
                st.rerun()
        else:
            st.info(f"⏳ Status Atual: **{current_status}**")
            st.write("O Agente de IA validou o pedido. Aguardando libertação de fundos pelo Oficial da Seguradora.")
            if st.button("🔄 Atualizar Status"): 
                st.rerun()

# --- PORTAL DO OFICIAL ---
elif st.session_state.role == 'oficial':
    st.sidebar.button("⬅️ Sair do Portal", on_click=lambda: st.session_state.update({"role": None}))
    st.title("🏢 Insurance Officer Dashboard")
    
    st.subheader("📋 Sinistros Pré-Aprovados pela IA")
    
    # LISTAR PENDENTES (API ou Memória Local)
    try:
        pendentes = requests.get(f"{API_URL}/api/oficial/pendentes", timeout=2).json()
    except:
        pendentes = [v for k, v in st.session_state.fila_cloud.items() if v['status'] == "Aguardando Oficial"]

    if not pendentes:
        st.info("Não existem sinistros pendentes de autorização.")
    
    for item in pendentes:
        with st.container(border=True):
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"#### Sinistro #{item['id']} - :green[✅ IA VALIDOU]")
                st.write(f"**Cliente:** {item.get('cliente')} | **Valor:** $50.00 USD")
                with st.expander("👁️ Ver Auditoria da IA (Logs de Decisão)"):
                    for passo in item.get('raciocinio', []):
                        st.write(f"⚙️ {passo}")
            with col_btn:
                if st.button(f"💸 Autorizar", key=f"btn_{item['id']}"):
                    with st.spinner("🔐 Acessando Token Vault e processando Payout..."):
                        try:
                            res_pay = requests.post(f"{API_URL}/api/oficial/autorizar/{item['id']}").json()
                            payout_id = res_pay.get('payout_id')
                        except:
                            # Execução Direta para Deploy
                            suc, msg = acionar_pagamento_com_paypal(valor_usd=50)
                            payout_id = msg.split("ID: ")[-1] if suc else "ERRO"
                            if item['id'] in st.session_state.fila_cloud:
                                st.session_state.fila_cloud[item['id']]["status"] = "Pago"
                                st.session_state.fila_cloud[item['id']]["payout_id"] = payout_id
                        
                        st.session_state.sucesso_oficial = payout_id
                        st.rerun()

    st.markdown("---")
    st.header("⚙️ Gestão de Credenciais")
    if "code" not in query_params:
        st.warning("⚠️ Cofre PayPal fechado. Ligue-se para autorizar pagamentos.")
        params = {
            "response_type": "code", 
            "client_id": AUTH0_CLIENT_ID, 
            "connection": "paypal-sandbox", 
            "redirect_uri": REDIRECT_URI, 
            "state": "role=oficial"
        }
        st.link_button("🔑 Abrir Cofre PayPal (Auth0 Vault)", f"https://{AUTH0_DOMAIN}/authorize?{urlencode(params)}")
    else:
        st.success("🔒 Auth0 Token Vault: Ativo e Seguro.")
        if 'sucesso_oficial' in st.session_state:
            st.balloons()
            st.success(f"Pagamento efetuado com sucesso! ID: {st.session_state.sucesso_oficial}")
            if st.button("Limpar Notificação"): 
                del st.session_state.sucesso_oficial
                st.rerun()