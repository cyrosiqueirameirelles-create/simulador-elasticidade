# jogo_elasticidade.py
import streamlit as st
import numpy as np
import random

st.set_page_config(page_title="Jogo da Elasticidade", layout="centered")

# =================== CONFIGURAÇÃO DO JOGO ===================
produtos = {
    "Notebook de entrada": {
        "Estudante": {"a": 12000, "b": 5.8},
        "Família":   {"a":  9500, "b": 3.6},
        "Empresa":   {"a":  7000, "b": 2.4},
    },
    "TV 50\" básica": {
        "Estudante": {"a":  8000, "b": 3.8},
        "Família":   {"a": 14000, "b": 5.2},
        "Empresa":   {"a":  4000, "b": 1.5},
    },
    "Cadeira ergonômica PRO": {
        "Estudante": {"a":  6000, "b": 2.8},
        "Família":   {"a":  7500, "b": 3.4},
        "Empresa":   {"a": 11000, "b": 4.5},
    },
}

cenarios = {
    "Base": 1.0,
    "Alta renda": 1.1,
    "Crédito fácil": 1.2,
    "Recessão": 0.85
}

p_min, p_max, p_step = 1000, 3000, 50

# Funções
def q_linear(a, b, p, shock=1.0):
    return max(0, (a * shock) - b * p)

def receita_total(produto, preco, shock):
    total = 0
    for cfg in produto.values():
        total += preco * q_linear(cfg["a"], cfg["b"], preco, shock)
    return total

# =================== ESTADO DO JOGO ===================
if "jogo_iniciado" not in st.session_state:
    st.session_state.jogo_iniciado = False
    st.session_state.tentativas = 0
    st.session_state.escolhido = None
    st.session_state.cenario_escolhido = None
    st.session_state.preco_otimo = None
    st.session_state.historico = []

# =================== INÍCIO DO JOGO ===================
st.title("🎯 Jogo da Elasticidade-Preço")
st.write("Objetivo: descubra o **preço que maximiza a receita** para um produto misterioso!")

if not st.session_state.jogo_iniciado:
    if st.button("▶️ Iniciar Jogo"):
        # Escolhe produto e cenário aleatórios
        st.session_state.escolhido = random.choice(list(produtos.keys()))
        st.session_state.cenario_escolhido = random.choice(list(cenarios.keys()))
        shock = cenarios[st.session_state.cenario_escolhido]
        
        # Calcula preço ótimo
        precos = np.arange(p_min, p_max + p_step, p_step)
        receitas = [receita_total(produtos[st.session_state.escolhido], p, shock) for p in precos]
        st.session_state.preco_otimo = precos[np.argmax(receitas)]
        
        st.session_state.jogo_iniciado = True
        st.session_state.tentativas = 0
        st.session_state.historico = []
else:
    shock = cenarios[st.session_state.cenario_escolhido]
    st.markdown(f"**Produto:** {st.session_state.escolhido}  |  **Cenário:** {st.session_state.cenario_escolhido}")
    preco_input = st.number_input("💰 Escolha um preço (R$)", p_min, p_max, step=p_step)

    if st.button("Chutar preço"):
        st.session_state.tentativas += 1
        receita = receita_total(produtos[st.session_state.escolhido], preco_input, shock)
        st.session_state.historico.append((preco_input, receita))

        # Feedback
        if preco_input == st.session_state.preco_otimo:
            st.success(f"🎉 Perfeito! Você acertou o preço ótimo: R$ {preco_input}")
            st.balloons()
            st.session_state.jogo_iniciado = False
        else:
            dica = "⬆️ Suba o preço" if preco_input < st.session_state.preco_otimo else "⬇️ Abaixe o preço"
            st.warning(f"Receita: R$ {receita:,.0f}  |  {dica}".replace(",", "."))
            
            if st.session_state.tentativas >= 3:
                st.error(f"💀 Fim de jogo! O preço ótimo era **R$ {st.session_state.preco_otimo}**")
                st.session_state.jogo_iniciado = False

    # Histórico
    if st.session_state.historico:
        st.subheader("📜 Histórico de tentativas")
        hist_df = pd.DataFrame(st.session_state.historico, columns=["Preço", "Receita"])
        st.table(hist_df)
