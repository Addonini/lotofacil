import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client

st.set_page_config(page_title="Lotofácil Analytics", page_icon="🟣", layout="wide")

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: Client = init_connection()

@st.cache_data(ttl=300)
def load_data():
    res = supabase.table("lotofacil").select("*").order("id", desc=False).execute()
    return pd.DataFrame(res.data)

def buscar_meus_jogos():
    res = supabase.table("meus_jogos_lotofacil").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data)

df = load_data()
if df.empty:
    st.warning("Nenhum sorteio da Lotofácil encontrado. Rode o robô!")
    st.stop()

ultimo_concurso = df.iloc[-1]
prox_concurso = int(ultimo_concurso['id']) + 1

st.title("🟣 Painel Analítico da Lotofácil")
st.markdown(f"**Último Concurso:** {int(ultimo_concurso['id'])} | **Data:** {ultimo_concurso.get('data_sorteio', '')}")

aba_dash, aba_gerador, aba_conferidor = st.tabs(["📊 Dashboard", "🔮 Gerador Inteligente", "✅ Conferidor"])

# ==========================================
# ABA 1: DASHBOARD
# ==========================================
with aba_dash:
    st.subheader(f"📌 Resultado do Concurso {int(ultimo_concurso['id'])}")
    bolas_sorteadas = [int(ultimo_concurso[f'bola_{i}']) for i in range(1, 16)]
    
    # Exibindo em 3 linhas de 5 bolas para ficar bonito
    for i in range(0, 15, 5):
        cols = st.columns(5)
        for j in range(5):
            cols[j].success(f"**{bolas_sorteadas[i+j]:02d}**")

    # Calcula Frequências
    lista_colunas = [df[f'bola_{i}'] for i in range(1, 16)]
    todas_as_bolas = pd.concat(lista_colunas)
    frequencias = todas_as_bolas.value_counts().reset_index()
    frequencias.columns = ['Número', 'Vezes Sorteado']
    
    todos_numeros = pd.DataFrame({'Número': range(1, 26)})
    frequencias = pd.merge(todos_numeros, frequencias, on='Número', how='left').fillna(0)
    frequencias_ordenadas = frequencias.sort_values(by='Vezes Sorteado', ascending=False)

    st.divider()
    st.subheader("📊 Frequência Histórica (As 25 Dezenas)")
    st.bar_chart(data=frequencias.set_index('Número'))

# ==========================================
# ABA 2: GERADOR
# ==========================================
with aba_gerador:
    st.subheader("🔮 Filtro Heurístico (Lotofácil)")
    st.write("Filtra descartando jogos que fogem do padrão matemático: exige 7 ou 8 números ímpares e de 4 a 6 números primos.")
    
    concurso_alvo = st.number_input("Para qual concurso?", min_value=1, value=prox_concurso, step=1)
    
    if st.button("🎲 Gerar 5 Palpites"):
        pesos = frequencias['Vezes Sorteado'].values + 1
        pesos_normalizados = pesos / pesos.sum()
        
        jogos_gerados = []
        primos = [2, 3, 5, 7, 11, 13, 17, 19, 23]
        
        with st.spinner("Aplicando filtros de Ímpares e Primos..."):
            while len(jogos_gerados) < 5:
                # Lotofácil: Sorteia 15 de 25
                palpite = np.random.choice(frequencias['Número'].values, size=15, replace=False, p=pesos_normalizados)
                
                # REGRA 1: Ímpares (Padrão histórico é 7 ou 8 ímpares)
                impares = sum(1 for x in palpite if x % 2 != 0)
                if impares not in [7, 8]: continue
                
                # REGRA 2: Primos (Padrão histórico é de 4 a 6 primos)
                qtd_primos = sum(1 for x in palpite if x in primos)
                if qtd_primos not in [4, 5, 6]: continue
                
                palpite = list(palpite)
                palpite.sort()
                
                if palpite not in jogos_gerados:
                    jogos_gerados.append(palpite)

        st.session_state['loto_temp'] = jogos_gerados
        st.session_state['loto_conc'] = concurso_alvo
        st.balloons()

    if 'loto_temp' in st.session_state:
        st.success(f"🎯 5 Jogos gerados para o Concurso {st.session_state['loto_conc']}!")
        for i, jogo in enumerate(st.session_state['loto_temp']):
            jogo_str = " - ".join([f"{x:02d}" for x in jogo])
            st.markdown(f"**Jogo {i+1}:** `{jogo_str}`")
            
        if st.button("💾 Salvar Palpites"):
            for jogo in st.session_state['loto_temp']:
                registro = {"concurso": st.session_state['loto_conc']}
                for i in range(15):
                    registro[f"bola_{i+1}"] = int(jogo[i])
                supabase.table("meus_jogos_lotofacil").insert(registro).execute()
            
            del st.session_state['loto_temp']
            st.success("Salvo! Vá para o Conferidor.")
            st.rerun()

# ==========================================
# ABA 3: CONFERIDOR
# ==========================================
with aba_conferidor:
    st.subheader("✅ Conferidor Oficial")
    
    meus_jogos = buscar_meus_jogos()
    if meus_jogos.empty or 'concurso' not in meus_jogos.columns:
        st.info("Nenhum jogo salvo.")
    else:
        jogos_validos = meus_jogos.dropna(subset=['concurso'])
        concursos = sorted([int(c) for c in jogos_validos['concurso'].unique()], reverse=True)
        sel_conc = st.selectbox("Selecione o concurso:", concursos)
        
        jogos_filtrados = jogos_validos[jogos_validos['concurso'] == sel_conc]
        st.write(f"Você tem **{len(jogos_filtrados)}** jogo(s) neste concurso.")
        
        res_oficial = df[df['id'] == sel_conc]
        
        if res_oficial.empty:
            st.warning("⏳ Sorteio ainda não realizado (ou robô não rodou).")
            for _, row in jogos_filtrados.iterrows():
                meu = [int(row[f'bola_{i}']) for i in range(1, 16)]
                st.markdown("- `" + " - ".join([f"{x:02d}" for x in sorted(meu)]) + "`")
        else:
            oficial_set = set([int(res_oficial.iloc[0][f'bola_{i}']) for i in range(1, 16)])
            
            for _, row in jogos_filtrados.iterrows():
                meu_set = set([int(row[f'bola_{i}']) for i in range(1, 16)])
                acertos = oficial_set.intersection(meu_set)
                qtd = len(acertos)
                
                jogo_str = " ".join([f"{x:02d}" for x in sorted(list(meu_set))])
                
                if qtd == 15: cor, txt = "green", "🏆 15 ACERTOS - MILIONÁRIO!"
                elif qtd == 14: cor, txt = "orange", "🏅 14 ACERTOS!"
                elif qtd in [11, 12, 13]: cor, txt = "blue", f"💸 {qtd} Acertos (Prêmio Fixo)"
                else: cor, txt = "red", f"❌ {qtd} acertos"
                
                st.markdown(f"**Bilhete:** `{jogo_str}`  ➡️  :{cor}[**{txt}**]")
                st.divider()
