# app.py
# Requisitos: streamlit, numpy, matplotlib, pandas
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import random

# =========================================================
# =============== CONFIGURAÇÃO GERAL/ESTILO ===============
# =========================================================
st.set_page_config(page_title="Elasticidade-Preço — Simulador + Jogo", layout="wide")
COL_BG = "#0f1116"; COL_FG = "#cfd6e6"; COL_GRID = "#2a3146"; COL_VLINE = "#c33d3d"

def kpi_fmt_num(x): return f"{x:,.0f}".replace(",", ".")
def kpi_fmt_moeda(x): return f"R$ {x:,.0f}".replace(",", ".")

# =========================================================
# ===================== BASE DE DADOS =====================
# =========================================================
# a e b calibrados para faixa de 1.000–3.000, com choques multiplicativos em a (nível de demanda).
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

# Faixa de preços padrão
P_MIN, P_MAX, P_STEP = 1000, 3000, 50
PRECOS = np.arange(P_MIN, P_MAX + P_STEP, P_STEP)

# =========================================================
# ===================== FUNÇÕES DE MODELO =================
# =========================================================
def q_linear(a, b, p, shock=1.0):
    """Demanda linear Q = max(0, s·a − b·P). Aceita escalar/vetor em p."""
    return np.maximum(0, (a * shock) - b * p)

def e_pontual(a, b, p, shock=1.0):
    """Elasticidade pontual E = (dQ/dP)·(P/Q) = (−b)·(P/Q)."""
    q = q_linear(a, b, p, shock)
    with np.errstate(divide="ignore", invalid="ignore"):
        E = -b * (p / q)
        E = np.where(q <= 0, np.nan, E)
    return E

def receita_total_por_perfil(a, b, p, shock=1.0):
    """Receita por perfil = P·Q."""
    q = q_linear(a, b, p, shock)
    return p * q

def receita_total_agregada(perfis, p, shock=1.0):
    """Receita total (somando perfis) para um preço P."""
    return sum(receita_total_por_perfil(cfg["a"], cfg["b"], p, shock) for cfg in perfis.values())

def classifica_elast(E):
    if np.isnan(E): return "sem demanda"
    e = abs(E)
    if e > 1: return "elástica (>1)"
    if e < 1: return "inelástica (<1)"
    return "unitária (=1)"

def otimo_agregado(perfis, shock=1.0):
    """
    Para demandas lineares agregadas, D_ag(P) = s*Σa_i − (Σb_i)·P.
    Receita R(P) = P·D_ag(P) = P·(sΣa − (Σb)P) → máximo em P* = (sΣa)/(2Σb).
    """
    soma_a = sum(cfg["a"] for cfg in perfis.values())
    soma_b = sum(cfg["b"] for cfg in perfis.values())
    if soma_b <= 0: 
        return None, None, None  # não deveria acontecer
    p_star = (shock * soma_a) / (2.0 * soma_b)
    p_star = float(np.clip(p_star, P_MIN, P_MAX))  # restringe à faixa da UI
    r_star = float(receita_total_agregada(perfis, p_star, shock))
    # Elasticidade agregada unitária no ótimo
    return p_star, r_star, (soma_a*shock, soma_b)

def ponto_unitario_por_perfil(cfg, shock=1.0):
    """Para Q=a−bP → R=P(a−bP). Máximo em P=a/(2b). É o ponto de elasticidade unitária do perfil."""
    a, b = cfg["a"], cfg["b"]
    if b <= 0: return None
    p_u = (a * shock) / (2.0 * b)
    return float(np.clip(p_u, P_MIN, P_MAX))

def narrativa_coach(produto, preco, shock_label, series, p_star, r_star, r_atual):
    pct = 0.0 if (r_star is None or r_star == 0) else (r_atual / r_star)
    alvo = "no **ótimo**" if abs(preco - p_star) < 1e-9 else ("**abaixar**" if preco > p_star else "**subir**")
    mais_sens = max(series.items(), key=lambda kv: abs(kv[1]["E"]) if not np.isnan(kv[1]["E"]) else -1)[0]
    mais_est = min(series.items(), key=lambda kv: abs(kv[1]["E"]) if not np.isnan(kv[1]["E"]) else 999)[0]
    return (
        f"No **{produto}** em **{shock_label}**, você está com **{kpi_fmt_moeda(preco)}**. "
        f"Isso rende **{pct:,.1%}** da *receita máxima* (gap: {kpi_fmt_moeda(abs(preco - p_star))} do \(P^*\)). "
        f"O perfil mais sensível é **{mais_sens}**, e o mais estável é **{mais_est}**. "
        f"Para melhorar agora, tendência é **{ 'abaixar' if preco > p_star else 'subir' } preço** rumo a **{kpi_fmt_moeda(p_star)}**."
    ).replace(",", ".")

# =========================================================
# ================== CONTROLES GLOBAIS (UI) ===============
# =========================================================
st.sidebar.header("⚙️ Controles Globais")
preco = st.sidebar.slider("💰 Preço selecionado (R$)", P_MIN, P_MAX, 1800, P_STEP)
cenario_label = st.sidebar.selectbox("🌎 Cenário macroeconômico", list(CENARIOS.keys()))
shock = CENARIOS[cenario_label]

# =========================================================
# ====================== SIMULADOR PRO ====================
# =========================================================
st.markdown("<h1 style='text-align:center;'>📊 Simulador PRO de Elasticidade-Preço</h1>", unsafe_allow_html=True)
tabs = st.tabs(list(PRODUTOS.keys()))

for tab, produto in zip(tabs, PRODUTOS.keys()):
    with tab:
        perfis = PRODUTOS[produto]

        # ---- Cálculos por perfil ----
        series = {}
        for nome, cfg in perfis.items():
            qs = q_linear(cfg["a"], cfg["b"], PRECOS, shock)
            q_atual = float(q_linear(cfg["a"], cfg["b"], preco, shock))
            E_atual = float(e_pontual(cfg["a"], cfg["b"], preco, shock))
            R_atual = float(receita_total_por_perfil(cfg["a"], cfg["b"], preco, shock))
            series[nome] = {"qs": qs, "q_atual": q_atual, "E": E_atual, "R": R_atual, "cor": cfg["cor"], "cfg": cfg}

        # ---- Ótimo agregado e métrica de desempenho ----
        p_star, r_star, (A_s, B_s) = otimo_agregado(perfis, shock)
        r_total_atual = sum(v["R"] for v in series.values())
        pct_max = 0.0 if (r_star is None or r_star == 0) else (r_total_atual / r_star)

        # ---- KPIs topo ----
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Produto", produto)
        c2.metric("Preço atual", kpi_fmt_moeda(preco))
        c3.metric("Receita total", kpi_fmt_moeda(r_total_atual))
        c4.metric("% da máxima", f"{pct_max*100:,.1f}%".replace(",", "."))
        c5.metric("Preço ótimo (agregado)", kpi_fmt_moeda(p_star))

        # ---- Gráfico 1: Curvas de Demanda + pontos unitários ----
        with st.container(border=True):
            fig, ax = plt.subplots(figsize=(10, 5.6))
            fig.patch.set_facecolor(COL_BG); ax.set_facecolor(COL_BG)

            for nome, s in series.items():
                cor = s["cor"]
                ax.plot(PRECOS, s["qs"], label=f"Demanda — {nome}", color=cor, linewidth=2.0)
                ax.scatter([preco], [s["q_atual"]], color=cor, s=60, zorder=5)
                # Ponto unitário do perfil
                p_u = ponto_unitario_por_perfil(s["cfg"], shock)
                if p_u is not None:
                    q_u = q_linear(s["cfg"]["a"], s["cfg"]["b"], p_u, shock)
                    ax.scatter([p_u], [q_u], color=cor, s=45, marker="X", zorder=6)

            # Linha do preço atual + unitário agregado
            ax.axvline(preco, color=COL_VLINE, linestyle="--", linewidth=1.4, label="Preço selecionado")
            # Unitário agregado: p* também é o unitário da curva agregada
            if p_star is not None:
                q_star = sum(q_linear(cfg["a"], cfg["b"], p_star, shock) for cfg in perfis.values())
                ax.scatter([p_star], [q_star], color="#ffffff", s=70, marker="D", zorder=7, label="Unitário (agregado)")

            ax.grid(color=COL_GRID, linestyle=":", linewidth=0.8, alpha=0.7)
            ax.set_xlabel("Preço (R$)", color=COL_FG); ax.set_ylabel("Quantidade Demandada", color=COL_FG)
            ax.set_title(f"Curvas de Demanda — {produto}", color="white", pad=10, fontsize=18)
            ax.tick_params(colors=COL_FG)
            leg = ax.legend(facecolor="#1a1f2e", edgecolor=COL_GRID)
            for text in leg.get_texts(): text.set_color("#e6e6e6")
            st.pyplot(fig, use_container_width=True)

        # ---- Gráfico 2: Receita agregada vs. Preço com máximo ----
        with st.container(border=True):
            fig2, ax2 = plt.subplots(figsize=(10, 4.8))
            fig2.patch.set_facecolor(COL_BG); ax2.set_facecolor(COL_BG)
            R_curve = [receita_total_agregada(perfis, p, shock) for p in PRECOS]
            ax2.plot(PRECOS, R_curve, linewidth=2.4)
            ax2.axvline(p_star, color=COL_VLINE, linestyle="--", linewidth=1.4)
            ax2.scatter([p_star], [r_star], s=70, marker="o", zorder=5)
            ax2.scatter([preco], [r_total_atual], s=50, marker="s", zorder=5)
            ax2.grid(color=COL_GRID, linestyle=":", linewidth=0.8, alpha=0.7)
            ax2.set_xlabel("Preço (R$)", color=COL_FG); ax2.set_ylabel("Receita agregada (R$)", color=COL_FG)
            ax2.set_title("Receita total vs. Preço (máximo destacado)", color="white", pad=10, fontsize=16)
            ax2.tick_params(colors=COL_FG)
            st.pyplot(fig2, use_container_width=True)

        # ---- Coach (narrativa) ----
        st.success(narrativa_coach(produto, preco, cenario_label, series, p_star, r_star, r_total_atual))

        # ---- Tabela resumo + download ----
        linhas = []
        for nome, s in series.items():
            linhas.append({
                "Perfil": nome,
                "Q (preço atual)": int(s["q_atual"]),
                "E (preço atual)": "-" if np.isnan(s["E"]) else f"{s['E']:.2f}",
                "Classificação": classifica_elast(s["E"]),
                "Receita (R$)": int(s["R"]),
                "P_unitário (≈ótimo do perfil)": "-" if ponto_unitario_por_perfil(s["cfg"], shock) is None 
                    else kpi_fmt_moeda(ponto_unitario_por_perfil(s["cfg"], shock))
            })
        df = pd.DataFrame(linhas)
        st.dataframe(df, use_container_width=True)
        st.download_button(
            "⬇️ Baixar CSV do resumo",
            df.to_csv(index=False).encode("utf-8"),
            file_name=f"resumo_{produto.replace(' ', '_')}.csv",
            mime="text/csv"
        )

# =========================================================
# ======================== JOGO ===========================
# =========================================================
st.markdown("---")
st.markdown("<h1 style='text-align:center;'>🎮 Jogo da Elasticidade-Preço</h1>", unsafe_allow_html=True)
st.caption("Objetivo: acertar o **preço que maximiza a receita agregada** (mesma lógica do simulador). Você tem **3 tentativas**.")

# Converte PRODUTOS para estrutura do jogo (sem cores)
PRODUTOS_JOGO = {prod: {k: {"a": v["a"], "b": v["b"]} for k, v in perfis.items()} for prod, perfis in PRODUTOS.items()}

def melhor_preco(perfis, shock=1.0):
    p_star, r_star, _ = otimo_agregado(perfis, shock)
    return p_star, r_star

def quente_morno_frio(dist):
    if dist <= 200:   return "🔥 **Quente**"
    if dist <= 500:   return "♨️ **Morno**"
    return "🧊 **Frio**"

def tendencia_local(perfis, p, shock):
    r_a = receita_total_agregada(perfis, p, shock)
    r_b = receita_total_agregada(perfis, min(p + P_STEP, P_MAX), shock)
    if abs(r_b - r_a) < 1e-9: return "neutra (perto do pico)"
    return "↑ sobe ao aumentar preço" if r_b > r_a else "↓ cai ao aumentar preço"

def faixa_texto(lo, hi, jitter=50):
    lo = max(P_MIN, lo - random.randint(0, jitter))
    hi = min(P_MAX, hi + random.randint(0, jitter))
    return f"R$ {int(lo)}–{int(hi)}"

# Estado do jogo
if "game" not in st.session_state:
    st.session_state.game = {
        "iniciado": False,
        "produto": None,
        "cenario": None,
        "shock": None,
        "p_star": None,
        "r_star": None,
        "tentativas": 0,
        "historico": [],  # (preco, receita, pct_max)
        "faixa_lo": P_MIN,
        "faixa_hi": P_MAX,
        "usou_dica": False
    }
G = st.session_state.game

# UI do jogo
cols_top = st.columns([1,1,1])
with cols_top[0]:
    iniciar = st.button("▶️ Iniciar Jogo")
with cols_top[1]:
    dica_btn = st.button("🎁 Dica única (1 por jogo)")
with cols_top[2]:
    reiniciar = st.button("🔁 Reiniciar")

if reiniciar:
    st.session_state.pop("game", None)
    st.rerun()

if iniciar and not G["iniciado"]:
    G["produto"] = random.choice(list(PRODUTOS_JOGO.keys()))
    cenario_jogo = random.choice(list(CENARIOS.keys()))
    G["cenario"] = cenario_jogo
    G["shock"] = CENARIOS[cenario_jogo]
    G["p_star"], G["r_star"] = melhor_preco(PRODUTOS_JOGO[G["produto"]], G["shock"])
    G["iniciado"] = True
    G["tentativas"] = 0
    G["historico"] = []
    G["faixa_lo"], G["faixa_hi"] = P_MIN, P_MAX
    G["usou_dica"] = False
    st.rerun()

if G["iniciado"]:
    st.markdown(f"**Produto:** {G['produto']}  |  **Cenário:** {G['cenario']}")
    preco_try = st.number_input("💰 Seu chute (R$)", min_value=P_MIN, max_value=P_MAX, step=P_STEP)

    if dica_btn and not G["usou_dica"]:
        largura = random.choice([500, 600, 700, 800])
        lo = max(P_MIN, G["p_star"] - largura//2)
        hi = min(P_MAX, G["p_star"] + largura//2)
        st.info(f"💡 **Dica:** o preço ótimo está **aproximadamente** entre **{faixa_texto(lo, hi, jitter=0)}**.")
        G["usou_dica"] = True
    elif dica_btn and G["usou_dica"]:
        st.warning("Você já usou sua dica única nesta rodada.")

    if st.button("Chutar preço"):
        G["tentativas"] += 1
        r = receita_total_agregada(PRODUTOS_JOGO[G["produto"]], preco_try, G["shock"])
        pct = (r / G["r_star"]) if G["r_star"] else 0.0
        G["historico"].append((preco_try, int(r), pct))

        dist = abs(preco_try - G["p_star"])
        termometro = quente_morno_frio(dist)
        direcao = "⬆️ Suba o preço" if preco_try < G["p_star"] else "⬇️ Abaixe o preço"
        st.warning(f"{termometro} | {direcao} | Você fez **{pct:,.1%}** da **receita máxima**.".replace(",", "."))
        st.caption(f"Tendência local: **{tendencia_local(PRODUTOS_JOGO[G['produto']], preco_try, G['shock'])}**.")

        # Estreita faixa provável com folga
        folga = random.choice([50, 100, 150])
        if preco_try < G["p_star"]:
            G["faixa_lo"] = max(G["faixa_lo"], preco_try + folga)
        else:
            G["faixa_hi"] = min(G["faixa_hi"], preco_try - folga)
        st.info(f"📎 **Faixa provável atual**: **{faixa_texto(G['faixa_lo'], G['faixa_hi'])}**")

        # Warmer/colder vs palpite anterior
        if len(G["historico"]) >= 2:
            prev_dist = abs(G["historico"][-2][0] - G["p_star"])
            if dist < prev_dist: st.success("👍 Você está **mais perto** do ótimo que no palpite anterior.")
            elif dist > prev_dist: st.error("👎 Você ficou **mais longe** do ótimo.")
            else: st.info("➡️ Mesma distância do palpite anterior.")

        # Check fim de jogo
        if preco_try == G["p_star"]:
            st.success(f"🎉 Acertou em cheio! **{kpi_fmt_moeda(G['p_star'])}** é o preço ótimo.")
            st.balloons()
            G["iniciado"] = False
        elif G["tentativas"] >= 3:
            st.error(f"💀 Fim de jogo! O preço ótimo era **{kpi_fmt_moeda(G['p_star'])}**.")
            st.caption("Nota: para demanda linear agregada, o pico da receita ocorre no ponto de **elasticidade unitária**.")
            G["iniciado"] = False

    # Histórico
    if G["historico"]:
        st.subheader("📜 Histórico de tentativas")
        hist = pd.DataFrame(G["historico"], columns=["Preço", "Receita", "% da Máxima"])
        hist["% da Máxima"] = (hist["% da Máxima"]*100).round(1).astype(str) + "%"
        st.table(hist)

# =========================================================
# ===================== RODAPÉ EXPLICATIVO =================
# =========================================================
with st.expander("📌 Como usamos IA generativa"):
    st.markdown("""
- A IA (ChatGPT) ajudou a estruturar o **modelo econômico**, a **otimização analítica** do preço-ótimo agregado, 
  o design do **dashboard** e a criação do **Jogo com Dicas**.
- O simulador e o jogo compartilham a mesma base de dados e funções, mantendo consistência conceitual.
- Destaques didáticos: **pontos unitários** dos perfis e do agregado, **curva de receita** com máximo, 
  **coach narrativo** e **métricas** claras para defender a lógica em banca.
""")
