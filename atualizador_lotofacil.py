import os
import requests
from datetime import datetime
from supabase import create_client, Client

URL_SUPABASE = os.environ.get("https://ubocevhrygpvzgxvbkqz.supabase.co")
KEY_SUPABASE = os.environ.get("sb_publishable_gA4yxBeUe3JBlP1WPCrW-g_2Bt_Fwth")

if not URL_SUPABASE or not KEY_SUPABASE:
    print("❌ ERRO: Chaves do Supabase não encontradas!")
    exit()

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

def buscar_ultimo_sorteio():
    print("📡 Buscando dados na API OFICIAL da Caixa (Lotofácil)...")
    url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0"}
    
    try:
        resposta = requests.get(url, headers=headers, verify=False)
        if resposta.status_code == 200:
            dados = resposta.json()
            data_formatada = datetime.strptime(dados["dataApuracao"], '%d/%m/%Y').strftime('%Y-%m-%d')
            
            # Pegando as 15 dezenas sorteadas
            dezenas = dados["listaDezenas"]
            
            registro = {
                "id": dados["numero"], 
                "data_sorteio": data_formatada,
            }
            # Preenche as 15 bolas dinamicamente
            for i in range(15):
                registro[f"bola_{i+1}"] = int(dezenas[i])
                
            return registro
        else:
            print(f"❌ Erro na API: Status {resposta.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return None

def salvar_no_banco(registro):
    if not registro: return
    try:
        supabase.table("lotofacil").upsert(registro).execute()
        print(f"✅ Sucesso! Concurso {registro['id']} salvo no Supabase.")
    except Exception as e:
        print(f"❌ Erro ao salvar no banco: {e}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    sorteio = buscar_ultimo_sorteio()
    salvar_no_banco(sorteio)
