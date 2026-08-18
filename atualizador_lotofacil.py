import os
import requests
from datetime import datetime
from supabase import create_client, Client

URL_SUPABASE = os.environ.get("https://ubocevhrygpvzgxvbkqz.supabase.co")
KEY_SUPABASE = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVib2NldmhyeWdwdnpneHZia3F6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNTA5OTksImV4cCI6MjEwMjYyNjk5OX0.Z-fA1jqlpFTGr3BhtiQhBX4wuUQHCnOVJez5N4GAmS0")

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
        print(f"Status da API da Caixa: {resposta.status_code}")
        
        if resposta.status_code == 200:
            dados = resposta.json()
            data_formatada = datetime.strptime(dados["dataApuracao"], '%d/%m/%Y').strftime('%Y-%m-%d')
            dezenas = dados["listaDezenas"]
            
            registro = {
                "id": int(dados["numero"]), 
                "data_sorteio": data_formatada,
            }
            for i in range(15):
                registro[f"bola_{i+1}"] = int(dezenas[i])
                
            print(f"📦 Dados extraídos com sucesso para o concurso: {registro['id']}")
            return registro
        else:
            print(f"❌ Erro na API da Caixa: Status {resposta.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro de conexão ao buscar API: {e}")
        return None

def salvar_no_banco(registro):
    if not registro: 
        print("⚠️ Nenhum registro para salvar.")
        return
        
    try:
        print("Tentando salvar no Supabase...")
        resposta_banco = supabase.table("lotofacil").upsert(registro).execute()
        print(f"✅ Sucesso absoluto! Resposta do Supabase: {resposta_banco}")
    except Exception as e:
        print(f"🚨 ERRO CRÍTICO AO SALVAR NO SUPABASE: {e}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    sorteio = buscar_ultimo_sorteio()
    salvar_no_banco(sorteio)
