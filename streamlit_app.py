# ====== JOGO COM DICAS ======
import streamlit as st
import numpy as np
import pandas as pd
import random

# Evita conflito se já chamou set_page_config em outra página
try:
    st.set_page_config(page_title="Jogo da Elasticidade", layout="centered")
except:
    pass

# ------------------ Parâmetros do jogo ------------------
produtos_jogo = {
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
cenarios_jogo = {"Base": 1.0, "Alta renda": 1.1, "Crédito fácil": 1.2, "Recessão": 0.85}

P_MIN, P_MAX, STEP = 1000, 3000, 50

# ------------------ Funções ------------------
def q_linear(a, b, p, shock=1.0):
    return max(0, (a * shock) - b * p)

def receita_total(produto_cfg, p, shock):
    return sum(p * q_linear(cfg["a"], cfg["b"], p, shock) for cfg in produto_cfg.values())

def melhor_preco(produto_cfg, shock):
    precos = np.arange(P_MIN, P_MAX + STEP, STEP)
    receitas = [receita_total(produto_cfg, p, shock) for p in precos]
    return precos[int(np.argmax(receitas))], max(receitas)

def quente_morno_frio(dist):
    if dist <= 200:   # quente (perto)
        return "🔥 **Quente**"
    if dist <= 500:   # morno
        return "♨️ **Morno**"
    return "🧊 **Frio**"  # longe

def tendencia_receita(produto_cfg, p, shock):
    # Derivada da receita total ~ R'(p) ≈ R(p+step)-R(p) (sinal)
    r_a = receita_total(produto_cfg, p, shock)
    r_b = receita_total(produto_cfg, min(p + STEP, P_MAX), shock)
    if abs(r_b - r_a) < 1e-9:
        return "neutra (perto do pico)"
    return "↑ sobe ao aumentar preço" if r_b > r_a else "↓ cai ao aumentar preço"

def faixa_texto(lo, hi, jitter=50):
    lo = max(P_MIN, lo - random.randint(0, jitter))
    hi = min(P_MAX, hi + random.randint(0, jitter))
    return f"R$ {lo}–{hi}"

# ------------------ Estado ------------------
if "game" not in st.session_state:
    st.session_state.game = {
        "iniciado": False,
        "tentativas": 0,
        "produto": None,
        "cenario": None,
        "shock": None,
        "p_otimo": None,
        "r_max": None,
        "historico": [],     # (preco, receita, pct_max)
        "lo": P_MIN,
        "hi": P_MAX,
        "usou_dica": False,
    }

G = st.session_state.game

# ------------------ UI ------------------
st.title("🎯 Jogo da Elasticidade-Preço (com dicas)")

if not G["iniciado"]:
    if st.button("▶️ Iniciar Jogo"):
        G["produto"] = random.choice(list(produtos_jogo.keys()))
        G["cenario"] = random.choice(list(cenarios_jogo.keys()))
        G["shock"] = cenarios_jogo[G["cenario"]]
        G["p_otimo"], G["r_max"] = melhor_preco(produtos_jogo[G["produto"]], G["shock"])
        G["iniciado"] = True
        G["tentativas"] = 0
        G["historico"] = []
        G["lo"], G["hi"] = P_MIN, P_MAX
        G["usou_dica"] = False
        st.rerun()
else:
    st.markdown(f"**Produto:** {G['produto']}  |  **Cenário:** {G['cenario']}")
    preco_input = st.number_input("💰 Seu chute (R$)", min_value=P_MIN, max_value=P_MAX, step=STEP)

    cols = st.columns([1,1,1])
    with cols[0]:
        tentar = st.button("Chutar preço")
    with cols[1]:
        dica_btn = st.button("🎁 Dica única (1 por jogo)")
    with cols[2]:
        desistir = st.button("🔁 Reiniciar")

    if desistir:
        st.session_state.pop("game", None)
        st.rerun()

    # Dica única: revela uma faixa aproximada adicional (sem números exatos)
    if dica_btn and not G["usou_dica"]:
        # abre uma faixa centrada no ótimo com largura ~ 500–800
        largura = random.choice([500, 600, 700, 800])
        lo = max(P_MIN, G["p_otimo"] - largura//2)
        hi = min(P_MAX, G["p_otimo"] + largura//2)
        st.info(f"💡 **Dica:** o preço ótimo está **aproximadamente** entre **{faixa_texto(lo, hi, jitter=0)}**.")
        G["usou_dica"] = True
    elif dica_btn and G["usou_dica"]:
        st.warning("Você já usou sua dica única nesta rodada.")

    if tentar:
        G["tentativas"] += 1
        r = receita_total(produtos_jogo[G["produto"]], preco_input, G["shock"])
        pct = r / G["r_max"] if G["r_max"] > 0 else 0.0
        G["historico"].append((preco_input, int(r), pct))

        # Direção + Quente/Morno/Frio + % da máxima
        dist = abs(preco_input - G["p_otimo"])
        termometro = quente_morno_frio(dist)
        direcao = "⬆️ Suba o preço" if preco_input < G["p_otimo"] else "⬇️ Abaixe o preço"
        st.warning(f"{termometro} | {direcao} | Você fez **{pct:,.1%}** da **receita máxima**.".replace(",", "."))

        # Tendência da receita (qualitativa)
        st.caption(f"Tendência local da receita: **{tendencia_receita(produtos_jogo[G['produto']], preco_input, G['shock'])}**.")

        # Estreitamento de faixa provável (com pequena folga)
        folga = random.choice([50, 100, 150])
        if preco_input < G["p_otimo"]:
            G["lo"] = max(G["lo"], preco_input + folga)
        else:
            G["hi"] = min(G["hi"], preco_input - folga)

        st.info(f"📎 **Faixa provável atual**: **{faixa_texto(G['lo'], G['hi'])}**")

        # Warmer/colder vs palpite anterior
        if len(G["historico"]) >= 2:
            prev_dist = abs(G["historico"][-2][0] - G["p_otimo"])
            if dist < prev_dist:
                st.success("👍 Você está **mais perto** do ótimo que no palpite anterior.")
            elif dist > prev_dist:
                st.error("👎 Você ficou **mais longe** em relação ao palpite anterior.")
            else:
                st.info("➡️ Mesma distância do palpite anterior.")

        # Fim de jogo: 3 tentativas
        if G["tentativas"] >= 3 and preco_input != G["p_otimo"]:
            st.error(f"💀 Fim de jogo! O preço ótimo era **R$ {G['p_otimo']}**.")
            st.caption("Dica técnica: em demandas lineares agregadas, a receita total maximiza por volta do ponto de elasticidade unitária agregada.")
            G["iniciado"] = False

        # Acertou na mosca
        if preco_input == G["p_otimo"]:
            st.success(f"🎉 Perfeito! Você acertou o preço ótimo: **R$ {G['p_otimo']}**")
            st.balloons()
            G["iniciado"] = False

    # Histórico compacto
    if G["historico"]:
        st.subheader("📜 Histórico")
        df = pd.DataFrame(G["historico"], columns=["Preço", "Receita", "% da Máxima"])
        df["% da Máxima"] = (df["% da Máxima"]*100).round(1).astype(str) + "%"
        st.table(df)
