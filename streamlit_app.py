# app.py
# Requirements: streamlit, numpy, matplotlib, pandas
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ===================== CONFIG =====================
st.set_page_config(page_title="Simulador de Elasticidade-Preço (3 Produtos)", layout="wide")

COL_BG = "#0f1116"; COL_FG = "#cfd6e6"; COL_GRID = "#2a3146"; COL_VLINE = "#c33d3d"

st.title("📊 Elasticidade-Preço por Produto e Perfil")
st.write("Escolha um **produto** e ajuste o **preço**. Cada aba mostra um gráfico e métricas para "
         "**Estudante**, **Família** e **Empresa**. Modelo: demanda linear *(Q = a − b·P)* e **elasticidade pontual**.")

# ===================== SIDEBAR (CALIBRAÇÃO GERAL) =====================
st.sidebar.header("⚙️ Controles gerais")
p_min, p_max, p_step = 1000, 3000, 50
preco = st.sidebar.slider("💰 Preço selecionado (R$)", min_value=p_min, max_value=p_max, value=1800, step=p_step)

st.sidebar.markdown("---")
st.sidebar.markdown("**Cenário (choque de demanda)**")
shock_label = st.sidebar.selectbox(
    "Cenário",
    ["Base (1.0)", "Alta renda (×1.1)", "Crédito fácil (×1.2)", "Recessão (×0.85)"],
    index=0
)
shock_map = {"Base (1.0)":1.0, "Alta renda (×1.1)":1.1, "Crédito fácil (×1.2)":1.2, "Recessão (×0.85)":0.85}
shock = shock_map[shock_label]

st.sidebar.markdown("---")
st.sidebar.caption("Dica: Ajuste **a** e **b** por produto abaixo (expander em cada aba).")

# ===================== PRODUTOS E PARÂMETROS INICIAIS =====================
# Valores pensados p/ 1k–3k (sem Q negativa no intervalo típico)
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

# ===================== FUNÇÕES (NumPy) =====================
def q_linear(a, b, p, shock=1.0):
    # p pode ser vetor; garante Q >= 0
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

def plot_produto(nome_produto, perfis_prod, preco_sel, shock, precos):
    # Cálculo
    series = {}
    for nome, cfg in perfis_prod.items():
        a, b = cfg["a"], cfg["b"]
        q_vec = q_linear(a, b, precos, shock)
        q_atual = float(q_linear(a, b, preco_sel, shock))
        E_atual = float(e_pontual(a, b, preco_sel, shock))
        R_atual = preco_sel * q_atual
        series[nome] = {"precos": precos, "qs": q_vec, "q_atual": q_atual, "E": E_atual, "R": R_atual, "cor": cfg["cor"]}

    # Cards topo
    q_total = sum(v["q_atual"] for v in series.values())
    r_total = sum(v["R"] for v in series.values())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Produto", nome_produto)
    c2.metric("Preço (R$)", f"{preco_sel:,.0f}".replace(",", "."))
    c3.metric("Q total", f"{int(q_total):,}".replace(",", "."))
    c4.metric("Receita total (R$)", f"{int(r_total):,}".replace(",", "."))

    # Gráfico
    with st.container(border=True):
        fig, ax = plt.subplots(figsize=(9.5, 5.3))
        fig.patch.set_facecolor(COL_BG); ax.set_facecolor(COL_BG)
        for nome, dados in series.items():
            ax.plot(dados["precos"], dados["qs"], label=f"Demanda — {nome}",
                    color=perfis_prod[nome]["cor"], linewidth=2.2)
            ax.scatter([preco_sel], [dados["q_atual"]], color=perfis_prod[nome]["cor"], s=60, zorder=5)
        ax.axvline(preco_sel, color=COL_VLINE, linestyle="--", linewidth=1.4, label="Preço selecionado")
        ax.grid(color=COL_GRID, linestyle=":", linewidth=0.8, alpha=0.7)
        ax.set_xlabel("Preço (R$)", color=COL_FG); ax.set_ylabel("Quantidade Demandada", color=COL_FG)
        ax.set_title(f"Curvas de Demanda — {nome_produto}", color="white", pad=10, fontsize=18)
        ax.tick_params(colors=COL_FG)
        leg = ax.legend(facecolor="#1a1f2e", edgecolor=COL_GRID)
        for text in leg.get_texts(): text.set_color("#e6e6e6")
        st.pyplot(fig, use_container_width=True)

    # Métricas por perfil
    st.subheader("Métricas no preço atual")
    cols = st.columns(3)
    linhas_tabela = []
    for i, (nome, dados) in enumerate(series.items()):
        q, E, R = dados["q_atual"], dados["E"], dados["R"]
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"### {nome}")
                st.markdown(f"- **Quantidade (Q):** {int(q):,}".replace(",", "."))
                st.markdown(f"- **Elasticidade (E):** {'—' if np.isnan(E) else f'{E:.2f}'}  \n"
                            f"  **Classificação:** {classifica(E)}")
                st.markdown(f"- **Receita (R = P×Q):** R$ {int(R):,}".replace(",", "."))
        linhas_tabela.append({
            "Perfil": nome,
            "Quantidade (Q)": int(q),
            "Elasticidade (E)": "-" if np.isnan(E) else f"{E:.2f}",
            "Classificação": classifica(E),
            "Receita (R$)": int(R)
        })
    st.dataframe(pd.DataFrame(linhas_tabela), use_container_width=True)

# ===================== NAVEGAÇÃO CLICÁVEL =====================
# Radio horizontal (além das abas) – dá pra clicar nas opções
selecionado = st.radio(
    "Selecione o produto:",
    list(produtos.keys()),
    horizontal=True,
    index=0
)

# Abas (clicáveis): um gráfico por produto
tabs = st.tabs(list(produtos.keys()))
precos_vec = np.arange(p_min, p_max + p_step, p_step)

for tab, nome_prod in zip(tabs, produtos.keys()):
    with tab:
        # Expander de calibração por produto
        with st.expander("Ajustar parâmetros (Q = a − b·P) deste produto"):
            col_a, col_b = st.columns(2)
            for perfil in produtos[nome_prod].keys():
                with col_a:
                    produtos[nome_prod][perfil]["a"] = st.number_input(f"{perfil} — a ({nome_prod})",
                                                                       value=float(produtos[nome_prod][perfil]["a"]),
                                                                       step=100.0)
                with col_b:
                    produtos[nome_prod][perfil]["b"] = st.number_input(f"{perfil} — b ({nome_prod})",
                                                                       value=float(produtos[nome_prod][perfil]["b"]),
                                                                       step=0.1, format="%.1f")
        plot_produto(nome_prod, produtos[nome_prod], preco, shock, precos_vec)

# Atalho: levar o usuário direto à aba escolhida no radio
# (Visualmente o radio já destaca a escolha; usamos como “âncora mental” p/ a banca)
st.info(f"📌 Produto selecionado no topo: **{selecionado}** | Cenário: **{shock_label}** | Preço: **R$ {preco:,.0f}**".replace(",", "."))

# ===================== IA GENERATIVA =====================
with st.expander("Como usamos IA generativa neste artefato"):
    st.markdown("""
- **ChatGPT** auxiliou na criação da estrutura multi-produto (abas clicáveis + rádio), funções vetorizadas (**NumPy**),
  layout em **Streamlit** (cards, containers, tabela) e documentação.
- Iteramos para calibrar **a** e **b** por produto e perfil, mantendo a faixa de **R$ 1.000–3.000** e cenários de choque.
- O resultado são **3 simuladores** (um por produto) com a mesma base teórica, facilitando a comparação e a defesa oral.
""")
