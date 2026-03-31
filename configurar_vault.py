import requests
import os
from dotenv import load_dotenv


load_dotenv()


DOMAIN = os.getenv("AUTH0_DOMAIN")
CLIENT_ID = os.getenv("AGENT_CLIENT_ID")
CLIENT_SECRET = os.getenv("AGENT_CLIENT_SECRET")

PAYPAL_SECRET_VALOR = os.getenv("PAYPAL_SECRET")

def injetar_chave_paypal():
    print("🔑 [Config] Iniciando injeção do segredo PayPal no Auth0 Token Vault...")
    
    if not PAYPAL_SECRET_VALOR:
        print("❌ Erro: PAYPAL_SECRET não encontrada no arquivo .env")
        return

    
    token_url = f"https://{DOMAIN}/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET, 
        "audience": f"https://{DOMAIN}/api/v2/",
        "grant_type": "client_credentials"
    }
    
    try:
        res = requests.post(token_url, json=payload).json()
        token = res.get('access_token')
        
        if not token:
            print(f"❌ Erro ao obter token: {res}")
            return

        
        
        vault_url = f"https://{DOMAIN}/api/v2/ai/token-vault/secrets"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        secret_data = {
            "name": "PAYPAL_SECRET",
            "value": PAYPAL_SECRET_VALOR  
        }

        response = requests.post(vault_url, json=secret_data, headers=headers)

        if response.status_code in [201, 200, 204]:
            print("✅ PINGÓ! O segredo do PayPal está agora protegido no Cofre Oficial do Auth0.")
        else:
            print(f"❌ Erro ao injetar no Vault: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Falha técnica na conexão: {str(e)}")

if __name__ == "__main__":
    injetar_chave_paypal()