# app.py
# Requisitos: streamlit, numpy, matplotlib, pandas
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import random

# ====================== CONFIG / ESTILO ======================
st.set_page_config(page_title="Elasticidade-Preço — Simulador + Jogo", layout="wide")
COL_BG = "#0f1116"; COL_FG = "#cfd6e6"; COL_GRID = "#2a3146"; COL_VLINE = "#c33d3d"

def fmt_num(x):   return f"{x:,.0f}".replace(",", ".")
def fmt_moeda(x): return f"R$ {x:,.0f}".replace(",", ".")

# ====================== DADOS DO MODELO ======================
PRODUTOS = {
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

CENARIOS = {
    "Base (1.0)": 1.0,
    "Alta renda (×1.1)": 1.1,
    "Crédito fácil (×1.2)": 1.2,
    "Recessão (×0.85)": 0.85
}

P_MIN, P_MAX, P_STEP = 1000, 3000, 50
PRECOS = np.arange(P_MIN, P_MAX + P_STEP, P_STEP)

# ====================== FUNÇÕES ECONÔMICAS ======================
def q_linear(a, b, p, shock=1.0):
    return np.maximum(0, (a * shock) - b * p)

def e_pontual(a, b, p, shock=1.0):
    q = q_linear(a, b, p, shock)
    with np.errstate(divide="ignore", invalid="ignore"):
        E = -b * (p / q)
        E = np.where(q <= 0, np.nan, E)
    return E

def receita_perfil(a, b, p, shock=1.0):
    q = q_linear(a, b, p, shock)
    return p * q

def receita_agregada(perfis, p, shock=1.0):
    return sum(receita_perfil(cfg["a"], cfg["b"], p, shock) for cfg in perfis.values())

def classifica(E):
    if np.isnan(E): return "sem demanda"
    e = abs(E)
    if e > 1: return "elástica (>1)"
    if e < 1: return "inelástica (<1)"
    return "unitária (=1)"

def otimo_agregado(perfis, shock=1.0):
    soma_a = sum(cfg["a"] for cfg in perfis.values())
    soma_b = sum(cfg["b"] for cfg in perfis.values())
    if soma_b <= 0:
        return None, None
    p_star = (shock * soma_a) / (2.0 * soma_b)
    p_star = float(np.clip(p_star, P_MIN, P_MAX))
    r_star = float(receita_agregada(perfis, p_star, shock))
    return p_star, r_star

def p_unitario_perfil(cfg, shock=1.0):
    a, b = cfg["a"], cfg["b"]
    if b <= 0: return None
    p_u = (a * shock) / (2.0 * b)
    return float(np.clip(p_u, P_MIN, P_MAX))

def narrativa(produto, preco, shock_label, series, p_star, r_star, r_atual):
    pct = 0.0 if not r_star else (r_atual / r_star)
    mais_sens = max(series.items(), key=lambda kv: abs(kv[1]["E"]) if not np.isnan(kv[1]["E"]) else -1)[0]
    mais_est  = min(series.items(), key=lambda kv: abs(kv[1]["E"]) if not np.isnan(kv[1]["E"]) else 999)[0]
    direcao   = "abaixar" if preco > p_star else ("subir" if preco < p_star else "manter")
    gap = abs(preco - p_star)
    return (
        f"No **{produto}** em **{shock_label}**, com **{fmt_moeda(preco)}** você obtém "
        f"**{pct:,.1%}** da receita máxima. Gap até \(P^*\): **{fmt_moeda(gap)}**. "
        f"Mais sensível: **{mais_sens}**; mais estável: **{mais_est}**. "
        f"Sugestão: **{direcao}** o preço em direção a **{fmt_moeda(p_star)}**."
    ).replace(",", ".")

# ====================== CABEÇALHO / INSTRUÇÕES ======================
st.markdown("### 🎯 Objetivo da atividade")
st.write(
    "Artefato interativo (simulador + jogo) para **elasticidade-preço**. "
    "Ajuste **preço** e **cenário** e veja como Estudante, Família e Empresa reagem, com impacto na **receita**."
)

# ====================== CONTROLES GLOBAIS ======================
st.sidebar.header("⚙️ Controles Globais")
preco = st.sidebar.slider("💰 Preço selecionado (R$)", P_MIN, P_MAX, 1800, P_STEP)
cenario_label = st.sidebar.selectbox("🌎 Cenário macroeconômico", list(CENARIOS.keys()))
shock = CENARIOS[cenario_label]

# ====================== SIMULADOR PRO ======================
st.markdown("## 📊 Simulador PRO")

tabs = st.tabs(list(PRODUTOS.keys()))
for tab, nome_prod in zip(tabs, PRODUTOS.keys()):
    with tab:
        perfis = PRODUTOS[nome_prod]

        # Cálculos por perfil
        series = {}
        for nome, cfg in perfis.items():
            qs = q_linear(cfg["a"], cfg["b"], PRECOS, shock)
            q_atual = float(q_linear(cfg["a"], cfg["b"], preco, shock))
            E_atual = float(e_pontual(cfg["a"], cfg["b"], preco, shock))
            R_atual = float(receita_perfil(cfg["a"], cfg["b"], preco, shock))
            series[nome] = {"qs": qs, "q_atual": q_atual, "E": E_atual, "R": R_atual, "cor": cfg["cor"], "cfg": cfg}

        # Ótimo agregado
        p_star, r_star = otimo_agregado(perfis, shock)
        r_total = sum(s["R"] for s in series.values())
        pct_max = 0.0 if not r_star else (r_total / r_star)

        # KPIs
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Produto", nome_prod)
        c2.metric("Preço atual", fmt_moeda(preco))
        c3.metric("Receita total", fmt_moeda(r_total))
        c4.metric("% da máxima", f"{pct_max*100:,.1f}%".replace(",", "."))
        c5.metric("Preço ótimo (agregado)", fmt_moeda(p_star))

        # Gráfico: Curvas de demanda + pontos unitários
        with st.container(border=True):
            fig, ax = plt.subplots(figsize=(10, 5.6))
            fig.patch.set_facecolor(COL_BG); ax.set_facecolor(COL_BG)

            for nome, s in series.items():
                cor = s["cor"]
                ax.plot(PRECOS, s["qs"], label=f"Demanda — {nome}", color=cor, linewidth=2.0)
                ax.scatter([preco], [s["q_atual"]], color=cor, s=60, zorder=5)
                p_u = p_unitario_perfil(s["cfg"], shock)
                if p_u is not None:
                    q_u = q_linear(s["cfg"]["a"], s["cfg"]["b"], p_u, shock)
                    ax.scatter([p_u], [q_u], color=cor, s=45, marker="X", zorder=6)

            ax.axvline(preco, color=COL_VLINE, linestyle="--", linewidth=1.4, label="Preço selecionado")
            if p_star is not None:
                q_star = sum(q_linear(cfg["a"], cfg["b"], p_star, shock) for cfg in perfis.values())
                ax.scatter([p_star], [q_star], color="#ffffff", s=70, marker="D", zorder=7, label="Unitário (agregado)")

            ax.grid(color=COL_GRID, linestyle=":", linewidth=0.8, alpha=0.7)
            ax.set_xlabel("Preço (R$)", color=COL_FG); ax.set_ylabel("Quantidade Demandada", color=COL_FG)
            ax.set_title(f"Curvas de Demanda — {nome_prod}", color="white", pad=10, fontsize=18)
            ax.tick_params(colors=COL_FG)
            leg = ax.legend(facecolor="#1a1f2e", edgecolor=COL_GRID)
            for text in leg.get_texts(): text.set_color("#e6e6e6")
            st.pyplot(fig, use_container_width=True)

        # Gráfico: Receita agregada vs preço
        with st.container(border=True):
            fig2, ax2 = plt.subplots(figsize=(10, 4.8))
            fig2.patch.set_facecolor(COL_BG); ax2.set_facecolor(COL_BG)
            R_curve = [receita_agregada(perfis, p, shock) for p in PRECOS]
            ax2.plot(PRECOS, R_curve, linewidth=2.4)
            ax2.axvline(p_star, color=COL_VLINE, linestyle="--", linewidth=1.4)
            ax2.scatter([p_star], [r_star], s=70, marker="o", zorder=5)
            ax2.scatter([preco], [r_total], s=50, marker="s", zorder=5)
            ax2.grid(color=COL_GRID, linestyle=":", linewidth=0.8, alpha=0.7)
            ax2.set_xlabel("Preço (R$)", color=COL_FG); ax2.set_ylabel("Receita agregada (R$)", color=COL_FG)
            ax2.set_title("Receita total vs. Preço (máximo destacado)", color="white", pad=10, fontsize=16)
            ax2.tick_params(colors=COL_FG)
            st.pyplot(fig2, use_container_width=True)

        # Narrativa
        st.success(narrativa(nome_prod, preco, cenario_label, series, p_star, r_star, r_total))

        # Tabela + download
        linhas = []
        for nome, s in series.items():
            linhas.append({
                "Perfil": nome,
                "Q (preço atual)": int(s["q_atual"]),
                "E (preço atual)": "-" if np.isnan(s["E"]) else f"{s['E']:.2f}",
                "Classificação": classifica(s["E"]),
                "Receita (R$)": int(s["R"]),
                "P_unitário perfil (≈ótimo individual)": "-" if p_unitario_perfil(s["cfg"], shock) is None
                    else fmt_moeda(p_unitario_perfil(s["cfg"], shock))
            })
        df = pd.DataFrame(linhas)
        st.dataframe(df, use_container_width=True)
        st.download_button("⬇️ Baixar CSV do resumo", df.to_csv(index=False).encode("utf-8"),
                           file_name=f"resumo_{nome_prod.replace(' ', '_')}.csv", mime="text/csv")

# ====================== JOGO (COM DICAS) ======================
st.markdown("---")
st.markdown("## 🎮 Jogo da Elasticidade-Preço")
st.caption("Acerte o **preço que maximiza a receita agregada**. Você tem **3 tentativas**. Use dicas — mas sem entregar o ouro 😉.")

# Estado default seguro (sincroniza chaves, evitando KeyError entre versões)
DEFAULT_GAME = {
    "iniciado": False,
    "produto": None,
    "cenario": None,
    "shock": None,
    "p_star": None,
    "r_star": None,
    "tentativas": 0,
    "historico": [],     # (preco, receita, pct_max)
    "faixa_lo": P_MIN,
    "faixa_hi": P_MAX,
    "usou_dica": False,
}
G = st.session_state.get("game", {}).copy()
# Preenche qualquer chave faltante
for k, v in DEFAULT_GAME.items():
    if k not in G:
        G[k] = v
st.session_state.game = G  # grava de volta sincronizado

def melhor_preco(perfis, shock):
    return otimo_agregado(perfis, shock)

def quente_morno_frio(dist):
    if dist <= 200: return "🔥 **Quente**"
    if dist <= 500: return "♨️ **Morno**"
    return "🧊 **Frio**"

def tendencia_local(perfis, p, shock):
    r_a = receita_agregada(perfis, p, shock)
    r_b = receita_agregada(perfis, min(p + P_STEP, P_MAX), shock)
    if abs(r_b - r_a) < 1e-9: return "neutra (perto do pico)"
    return "↑ sobe ao aumentar preço" if r_b > r_a else "↓ cai ao aumentar preço"

def faixa_texto(lo, hi, jitter=50):
    lo = max(P_MIN, lo - random.randint(0, jitter))
    hi = min(P_MAX, hi + random.randint(0, jitter))
    return f"R$ {int(lo)}–{int(hi)}"

# Botões topo
b1, b2, b3 = st.columns([1,1,1])
with b1:
    iniciar = st.button("▶️ Iniciar Jogo", type="primary", disabled=G.get("iniciado", False))
with b2:
    dica_btn = st.button(
        "🎁 Dica única",
        disabled=(not G.get("iniciado", False)) or G.get("usou_dica", False) or (G.get("p_star") is None)
    )
with b3:
    reiniciar = st.button("🔁 Reiniciar", disabled=not G.get("iniciado", False))

if reiniciar:
    st.session_state.game = DEFAULT_GAME.copy()
    st.rerun()

if iniciar:
    produtos_jogo = {prod: {k: {"a": v["a"], "b": v["b"]} for k, v in perfis.items()} for prod, perfis in PRODUTOS.items()}
    G["produto"] = random.choice(list(produtos_jogo.keys()))
    G["cenario"] = random.choice(list(CENARIOS.keys()))
    G["shock"]   = CENARIOS[G["cenario"]]
    G["p_star"], G["r_star"] = melhor_preco(produtos_jogo[G["produto"]], G["shock"])
    G["iniciado"] = True
    G["tentativas"] = 0
    G["historico"] = []
    G["faixa_lo"], G["faixa_hi"] = P_MIN, P_MAX
    G["usou_dica"] = False
    st.session_state.game = G
    st.rerun()

if dica_btn and G.get("iniciado", False) and (not G.get("usou_dica", False)) and (G.get("p_star") is not None):
    largura = random.choice([500, 600, 700, 800])
    lo = max(P_MIN, G["p_star"] - largura//2)
    hi = min(P_MAX, G["p_star"] + largura//2)
    st.info(f"💡 **Dica:** o preço ótimo está **aproximadamente** entre **{faixa_texto(lo, hi, jitter=0)}**.")
    G["usou_dica"] = True
    st.session_state.game = G

if G.get("iniciado", False):
    st.markdown(f"**Produto:** {G.get('produto')}  |  **Cenário:** {G.get('cenario')}")
    preco_try = st.number_input("💰 Seu chute (R$)", min_value=P_MIN, max_value=P_MAX, step=P_STEP)

    if st.button("Chutar preço"):
        # Segurança extra
        if (G.get("p_star") is None) or (G.get("r_star") is None):
            st.error("Estado do jogo incompleto. Clique em **Reiniciar** e depois em **Iniciar Jogo**.")
        else:
            produtos_jogo = {prod: {k: {"a": v["a"], "b": v["b"]} for k, v in perfis.items()} for prod, perfis in PRODUTOS.items()}
            perfis_escolhido = produtos_jogo[G["produto"]]
            r = receita_agregada(perfis_escolhido, preco_try, G["shock"])
            pct = (r / G["r_star"]) if G["r_star"] else 0.0

            G["tentativas"] = G.get("tentativas", 0) + 1
            G["historico"].append((preco_try, int(r), pct))

            dist = abs(preco_try - G["p_star"])
            termo = quente_morno_frio(dist)
            direcao = "⬆️ Suba o preço" if preco_try < G["p_star"] else "⬇️ Abaixe o preço"
            st.warning(f"{termo} | {direcao} | Você fez **{pct:,.1%}** da **receita máxima**.".replace(",", "."))
            st.caption(f"Tendência local: **{tendencia_local(perfis_escolhido, preco_try, G['shock'])}**.")

            # Estreitamento de faixa provável (com folga)
            folga = random.choice([50, 100, 150])
            if preco_try < G["p_star"]:
                G["faixa_lo"] = max(G["faixa_lo"], preco_try + folga)
            else:
                G["faixa_hi"] = min(G["faixa_hi"], preco_try - folga)
            st.info(f"📎 **Faixa provável atual**: **{faixa_texto(G['faixa_lo'], G['faixa_hi'])}**")

            # Warmer/colder
            if len(G["historico"]) >= 2:
                prev_dist = abs(G["historico"][-2][0] - G["p_star"])
                if dist < prev_dist: st.success("👍 Você está **mais perto** do ótimo que antes.")
                elif dist > prev_dist: st.error("👎 Você ficou **mais longe** do ótimo.")
                else: st.info("➡️ Mesma distância do palpite anterior.")

            # Fim de jogo
            if preco_try == G["p_star"]:
                st.success(f"🎉 Acertou em cheio! **{fmt_moeda(G['p_star'])}** é o preço ótimo.")
                st.balloons()
                G["iniciado"] = False
            elif G["tentativas"] >= 3:
                st.error(f"💀 Fim de jogo! O preço ótimo era **{fmt_moeda(G['p_star'])}**.")
                st.caption("Nota: na demanda linear agregada, a receita maximiza no ponto de **elasticidade unitária agregada**.")
                G["iniciado"] = False

            st.session_state.game = G  # persistir mudanças

    # Histórico
    if G.get("historico"):
        st.subheader("📜 Histórico de tentativas")
        hist = pd.DataFrame(G["historico"], columns=["Preço", "Receita", "% da Máxima"])
        hist["% da Máxima"] = (hist["% da Máxima"]*100).round(1).astype(str) + "%"
        st.table(hist)

# ====================== COMO USAMOS IA (PROF) ======================
with st.expander("📌 Como usamos IA generativa neste artefato"):
    st.markdown("""
- **Conceito:** *Elasticidade-preço da demanda* (apostila, seção 2.1).  
- **Uso da IA:** O ChatGPT ajudou a projetar o modelo (demanda linear por perfil), implementar a **otimização analítica** do preço ótimo agregado \\(P^* = \\tfrac{s\\sum a_i}{2\\sum b_i}\\), construir o **dashboard** em Streamlit e criar o **jogo** com dicas progressivas.
- **Aplicação:** Ajustando **preço** e **cenário**, visualizamos **quantidade**, **elasticidade** e **receita** por perfil e agregada; o **jogo** reforça o entendimento do ponto de **elasticidade unitária (receita máxima)**.
- **Comprovação:** cada integrante fará a postagem com foto no dia da apresentação.
""")
