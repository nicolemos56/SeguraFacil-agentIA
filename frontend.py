import streamlit as st
import requests
from urllib.parse import urlencode
import os
from dotenv import load_dotenv

#
load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
API_URL = os.getenv("API_URL")

st.set_page_config(page_title="SeguraFácil AgentIA", layout="wide", page_icon="🛡️")

# 
query_params = st.query_params

if "role" in query_params:
    st.session_state.role = query_params["role"]

if "code" in query_params and "role" not in query_params:
    st.session_state.role = 'oficial' 

# 
if 'role' not in st.session_state or st.session_state.role is None:
    st.title("🛡️ Welcome to SeguraFácil")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚖 INFORMAL WORKER PORTAL"):
            st.session_state.role = 'taxista'
            st.rerun()
    with col2:
        if st.button("🏢 INSURENCE OFFICER PORTAL"):
            st.session_state.role = 'oficial'
            st.rerun()

# 
elif st.session_state.role == 'taxista':
    st.sidebar.button("⬅️ Sair", on_click=lambda: st.session_state.update({"role": None}))
    st.title("🚖 Informal Worker Panel")
    
    if 'meu_sinistro_id' not in st.session_state:
        doc = st.file_uploader("Submeter Comprovativo", type=['png', 'jpg'])
        if st.button("Enviar para Análise"):
            if doc:
                with st.spinner("🤖 Agente de IA analisando documento..."):
                    temp_path = f"C:/temp/{doc.name}"
                    with open(temp_path, "wb") as f: f.write(doc.getbuffer())
                    payload = {"cliente_id": 123, "tipo_sinistro": "sangue", "documento_url": temp_path}
                    res = requests.post(f"{API_URL}/api/agente/submeter-sinistro", json=payload).json()
                    st.session_state.meu_sinistro_id = res['id']
                    st.rerun()
    else:
        status_res = requests.get(f"{API_URL}/api/sinistros/{st.session_state.meu_sinistro_id}").json()
        if status_res['status'] == "Pago":
            st.balloons()
            st.success("🎉 O SEU PAGAMENTO CHEGOU!")
            
            # 
            st.container(border=True).markdown(f"""
                ### 🧾 Recibo de Benefício
                **Status:** Pago via PayPal ✅  
                **Valor Transferido:** $50.00 USD  
                **ID Transação:** `{status_res['payout_id']}`
            """)
            
            if st.button("Submeter Novo"): 
                del st.session_state.meu_sinistro_id
                st.rerun()
        else:
            st.info(f"⏳ Status: {status_res['status']}. Aguardando oficial da seguradora...")
            if st.button("🔄 Atualizar Status"): st.rerun()

# 
elif st.session_state.role == 'oficial':
    st.sidebar.button("⬅️ Sair", on_click=lambda: st.session_state.update({"role": None}))
    
    # 
    st.subheader("📋 Lista de Sinistros para Autorização")
    pendentes = requests.get(f"{API_URL}/api/oficial/pendentes").json()
    
    if not pendentes:
        st.info("Nenhum sinistro pendente no momento.")
    
    for item in pendentes:
        status_color = "green" if item['status'] == "Aprovado" else "orange"
        badge = "✅ IA APROVOU" if item['status'] == "Aprovado" else "⚠️ IA ESCALOU"

        with st.container(border=True):
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"#### Sinistro #{item['id']} - :{status_color}[{badge}]")
                st.write(f"**Cliente ID:** {item['cliente']}")
                st.write(f"**Mensagem:** {item['detalhes']}")
                with st.expander("👁️ Ver Auditoria da IA (Logs de Decisão)"):
                    for passo in item.get('raciocinio', []):
                        st.write(f"⚙️ {passo}")
            with col_btn:
                if st.button(f"💸 Autorizar Payout", key=f"btn_{item['id']}"):
                    with st.spinner("🔐 Processando pagamento via Token Vault..."):
                        res_pay = requests.post(f"{API_URL}/api/oficial/autorizar/{item['id']}").json()
                        st.session_state.sucesso_oficial = res_pay.get('payout_id')
                        st.rerun()

    #
    st.markdown("---")
    st.header("🏢 Gestão da Seguradora")
    if "code" not in query_params:
        params = {"response_type": "code", "client_id": AUTH0_CLIENT_ID, "connection": "paypal-sandbox", "redirect_uri": "http://localhost:8501", "state": "role=oficial"}
        st.link_button("🔑 Abrir Cofre PayPal (Vault)", f"https://{AUTH0_DOMAIN}/authorize?{urlencode(params)}")
    else:
        st.success("🔒 Cofre Aberto. Pronto para autorizar.")
        if 'sucesso_oficial' in st.session_state:
            st.balloons()
            st.success(f"Pagamento realizado! ID: {st.session_state.sucesso_oficial}")
            if st.button("Limpar Notificação"): 
                del st.session_state.sucesso_oficial
                st.rerun()