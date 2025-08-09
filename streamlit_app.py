# app.py
# Requirements: streamlit, numpy, matplotlib, pandas
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ============== CONFIGURAÇÕES ==============
st.set_page_config(page_title="Simulador de Elasticidade-Preço", layout="wide")
COL_BG = "#0f1116"; COL_FG = "#cfd6e6"; COL_GRID = "#2a3146"; COL_VLINE = "#c33d3d"

# ============== TÍTULO ==============
st.markdown("<h1 style='text-align:center;'>📊 Simulador Interativo de Elasticidade-Preço</h1>", unsafe_allow_html=True)
st.write("Ajuste o **preço**, escolha o **produto** e veja como diferentes perfis de consumidores "
         "(Estudante, Família, Empresa) reagem. Use os **cenários** para simular mudanças no ambiente econômico.")

# ============== SIDEBAR ==============
st.sidebar.header("⚙️ Controles Globais")
p_min, p_max, p_step = 1000, 3000, 50
preco = st.sidebar.slider("💰 Preço selecionado (R$)", p_min, p_max, 1800, p_step)

cenarios = {
    "Base (1.0)": 1.0,
    "Alta renda (×1.1)": 1.1,
    "Crédito fácil (×1.2)": 1.2,
    "Recessão (×0.85)": 0.85
}
cenario_label = st.sidebar.selectbox("🌎 Cenário macroeconômico", list(cenarios.keys()))
shock = cenarios[cenario_label]

# ============== PRODUTOS E PARÂMETROS INICIAIS ==============
produtos = {
    "Notebook de entrada": {
        "Estudante": {"a": 12000, "b": 5.8, "cor": "#f7b500"},
        "Família":   {"a":  9500, "b": 3.6, "cor": "#38d39f"},
        "Empresa":   {"a":  7000, "b": 2.4, "cor": "#3aa0ff"},
    },
    "TV 50\" básica": {
        "Estudante": {"a":  8000, "b": 3.8, "cor": "#f7b500"},
        "Família":   {"a": 14000, "b": 5.2, "cor": "#38d39f"},
        "Empresa":   {"a":  4000, "b": 1.5, "cor": "#3aa0ff"},
    },
    "Cadeira ergonômica PRO": {
        "Estudante": {"a":  6000, "b": 2.8, "cor": "#f7b500"},
        "Família":   {"a":  7500, "b": 3.4, "cor": "#38d39f"},
        "Empresa":   {"a": 11000, "b": 4.5, "cor": "#3aa0ff"},
    },
}

# ============== FUNÇÕES (NumPy) ==============
def q_linear(a, b, p, shock=1.0):
    return np.maximum(0, (a * shock) - b * p)

def e_pontual(a, b, p, shock=1.0):
    q = q_linear(a, b, p, shock)
    with np.errstate(divide="ignore", invalid="ignore"):
        E = -b * (p / q)
        E = np.where(q <= 0, np.nan, E)
    return E

def classifica(E):
    if np.isnan(E): return "sem demanda"
    e_abs = abs(E)
    if e_abs > 1: return "elástica (>1)"
    if e_abs < 1: return "inelástica (<1)"
    return "unitária (=1)"

def narrativa(produto, series, preco, cenario):
    mais_elastica = max(series.items(), key=lambda x: abs(x[1]["E"]) if not np.isnan(x[1]["E"]) else -1)[0]
    mais_inelastica = min(series.items(), key=lambda x: abs(x[1]["E"]) if not np.isnan(x[1]["E"]) else 999)[0]
    return (f"No produto **{produto}**, ao preço de **R$ {preco:,.0f}**, o perfil mais sensível a preço é **{mais_elastica}**, "
            f"enquanto o mais estável é **{mais_inelastica}**. Cenário atual: **{cenario}**.")

# ============== PÁGINA PRINCIPAL COM ABAS ==============
abas = st.tabs(list(produtos.keys()))
precos_vec = np.arange(p_min, p_max + p_step, p_step)

for aba, nome_prod in zip(abas, produtos.keys()):
    with aba:
        perfis_prod = produtos[nome_prod]
        # Cálculos
        series = {}
        for nome, cfg in perfis_prod.items():
            a, b = cfg["a"], cfg["b"]
            q_vec = q_linear(a, b, precos_vec, shock)
            q_atual = float(q_linear(a, b, preco, shock))
            E_atual = float(e_pontual(a, b, preco, shock))
            R_atual = preco * q_atual
            series[nome] = {"precos": precos_vec, "qs": q_vec, "q_atual": q_atual, "E": E_atual, "R": R_atual, "cor": cfg["cor"]}

        # Métricas topo
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Produto", nome_prod)
        col2.metric("Preço", f"R$ {preco:,.0f}".replace(",", "."))
        col3.metric("Q Total", f"{sum(v['q_atual'] for v in series.values()):,.0f}".replace(",", "."))
        col4.metric("Receita Total", f"R$ {sum(v['R'] for v in series.values()):,.0f}".replace(",", "."))

        # Gráfico
        fig, ax = plt.subplots(figsize=(9.5, 5.3))
        fig.patch.set_facecolor(COL_BG); ax.set_facecolor(COL_BG)
        for nome, dados in series.items():
            ax.plot(dados["precos"], dados["qs"], label=f"Demanda — {nome}",
                    color=dados["cor"], linewidth=2.2)
            ax.scatter([preco], [dados["q_atual"]], color=dados["cor"], s=60, zorder=5)
        ax.axvline(preco, color=COL_VLINE, linestyle="--", linewidth=1.4, label="Preço selecionado")
        ax.grid(color=COL_GRID, linestyle=":", linewidth=0.8, alpha=0.7)
        ax.set_xlabel("Preço (R$)", color=COL_FG); ax.set_ylabel("Quantidade Demandada", color=COL_FG)
        ax.set_title(f"Curvas de Demanda — {nome_prod}", color="white", pad=10, fontsize=18)
        ax.tick_params(colors=COL_FG)
        leg = ax.legend(facecolor="#1a1f2e", edgecolor=COL_GRID)
        for text in leg.get_texts(): text.set_color("#e6e6e6")
        st.pyplot(fig, use_container_width=True)

        # Narrativa automática
        st.success(narrativa(nome_prod, series, preco, cenario_label))

        # Tabela
        tabela = []
        for nome, dados in series.items():
            tabela.append({
                "Perfil": nome,
                "Q": int(dados["q_atual"]),
                "E": "-" if np.isnan(dados["E"]) else f"{dados['E']:.2f}",
                "Classificação": classifica(dados["E"]),
                "Receita (R$)": int(dados["R"])
            })
        st.dataframe(pd.DataFrame(tabela), use_container_width=True)

        # Download CSV
        st.download_button(f"⬇️ Baixar dados ({nome_prod})", pd.DataFrame(tabela).to_csv(index=False).encode("utf-8"),
                           file_name=f"{nome_prod}_elasticidade.csv", mime="text/csv")

# ============== COMO USAMOS IA ==============
with st.expander("📌 Como usamos IA generativa"):
    st.markdown("""
- **ChatGPT** auxiliou em toda a arquitetura do código, uso de **NumPy** para cálculos vetorizados e design em **Streamlit**.
- Ajustamos parâmetros a e b por produto e perfil com apoio da IA, simulando diferentes sensibilidades a preço.
- Implementamos narrativa automática para análise instantânea.
- O resultado é um **dashboard interativo** com usabilidade profissional e visual de mercado.
""")

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
