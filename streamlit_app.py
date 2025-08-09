# app.py
# Requirements: streamlit, numpy, matplotlib, pandas
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ===================== CONFIG =====================
st.set_page_config(page_title="Simulador de Elasticidade-Preço", layout="wide")

# Paleta base
COL_BG = "#0f1116"
COL_FG = "#cfd6e6"
COL_GRID = "#2a3146"
COL_VLINE = "#c33d3d"

# ===================== TÍTULO =====================
st.title("📊 Simulador de Elasticidade-Preço da Demanda (3 Perfis)")
st.write(
    "Ajuste o **preço** e veja como **Estudante, Família e Empresa** reagem. "
    "O modelo usa demanda linear *(Q = a − b·P)* e calcula a **elasticidade pontual** em cada preço."
)

# ===================== SIDEBAR (CALIBRAÇÃO) =====================
st.sidebar.header("⚙️ Parâmetros do Modelo")

st.sidebar.markdown("**Preço** (faixa do simulador)")
p_min = 1000
p_max = 3000
p_step = 50
preco = st.sidebar.slider("💰 Preço selecionado (R$)", min_value=p_min, max_value=p_max, value=1800, step=p_step)

st.sidebar.markdown("---")
st.sidebar.markdown("**Curvas de demanda (Q = a − b·P)**")
# Valores default pensados para preços altos (1k–3k) sem Q negativa
a_est = st.sidebar.number_input("Estudante — a", value=9000, step=100)
b_est = st.sidebar.number_input("Estudante — b", value=3.8, step=0.1, format="%.1f")

a_fam = st.sidebar.number_input("Família — a", value=13000, step=100)
b_fam = st.sidebar.number_input("Família — b", value=4.8, step=0.1, format="%.1f")

a_emp = st.sidebar.number_input("Empresa — a", value=7000, step=100)
b_emp = st.sidebar.number_input("Empresa — b", value=2.2, step=0.1, format="%.1f")

st.sidebar.markdown("---")
st.sidebar.markdown("**Cenários (multiplicadores de demanda)**")
shock_label = st.sidebar.selectbox(
    "Cenário",
    ["Base (1.0)", "Alta renda (×1.1)", "Crédito fácil (×1.2)", "Recessão (×0.85)"],
    index=0
)
shock_map = {
    "Base (1.0)": 1.0,
    "Alta renda (×1.1)": 1.1,
    "Crédito fácil (×1.2)": 1.2,
    "Recessão (×0.85)": 0.85
}
shock = shock_map[shock_label]

# ===================== FUNÇÕES (com NumPy) =====================
def q_linear(a, b, p):
    # p pode ser escalar ou vetor; garante Q>=0
    return np.maximum(0, (a * shock) - b * p)

def e_pontual(a, b, p):
    q = q_linear(a, b, p)
    # E = (dQ/dP) * (P/Q) = (-b) * (P/Q)
    with np.errstate(divide="ignore", invalid="ignore"):
        E = -b * (p / q)
        E = np.where(q <= 0, np.nan, E)
    return E

def classifica(E):
    if np.isnan(E):
        return "sem demanda"
    e_abs = abs(E)
    if e_abs > 1:
        return "elástica (>1)"
    if e_abs < 1:
        return "inelástica (<1)"
    return "unitária (=1)"

# ===================== DADOS =====================
perfis = {
    "Estudante": {"a": a_est, "b": b_est, "cor": "#f7b500"},  # amarelo
    "Família":   {"a": a_fam, "b": b_fam, "cor": "#38d39f"},  # verde
    "Empresa":   {"a": a_emp, "b": b_emp, "cor": "#3aa0ff"},  # azul
}

precos = np.arange(p_min, p_max + p_step, p_step)

# Pré-cálculo p/ todos
series = {}
linhas_info = []
for nome, cfg in perfis.items():
    a, b, cor = cfg["a"], cfg["b"], cfg["cor"]
    q_vec = q_linear(a, b, precos)
    q_atual = float(q_linear(a, b, preco))
    E_atual = float(e_pontual(a, b, preco))
    R_atual = preco * q_atual

    series[nome] = {"precos": precos, "qs": q_vec, "q_atual": q_atual, "E": E_atual, "R": R_atual, "cor": cor}
    linhas_info.append((nome, q_atual, E_atual, R_atual, cor))

# ===================== RESUMO EM CARDS =====================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Preço selecionado (R$)", f"{preco:,.0f}".replace(",", "."))

# pega total e mostra
q_total = sum(x["q_atual"] for x in series.values())
r_total = sum(x["R"] for x in series.values())
c2.metric("Quantidade total", f"{int(q_total):,}".replace(",", "."))
c3.metric("Receita total (R$)", f"{int(r_total):,}".replace(",", "."))
c4.metric("Cenário", shock_label)

# ===================== GRÁFICO =====================
st.subheader("Curvas de Demanda por Perfil")
with st.container(border=True):
    fig, ax = plt.subplots(figsize=(9.5, 5.3))
    fig.patch.set_facecolor(COL_BG)
    ax.set_facecolor(COL_BG)

    for nome, dados in series.items():
        ax.plot(dados["precos"], dados["qs"], label=f"Demanda — {nome}",
                color=perfis[nome]["cor"], linewidth=2.2)
        ax.scatter([preco], [dados["q_atual"]], color=perfis[nome]["cor"], s=60, zorder=5)

    ax.axvline(preco, color=COL_VLINE, linestyle="--", linewidth=1.4, label="Preço selecionado")

    ax.grid(color=COL_GRID, linestyle=":", linewidth=0.8, alpha=0.7)
    ax.set_xlabel("Preço (R$)", color=COL_FG)
    ax.set_ylabel("Quantidade Demandada", color=COL_FG)
    ax.set_title("Demanda Linear com Elasticidade Pontual no Preço Selecionado", color="white", pad=10, fontsize=18)
    ax.tick_params(colors=COL_FG)
    leg = ax.legend(facecolor="#1a1f2e", edgecolor=COL_GRID)
    for text in leg.get_texts():
        text.set_color("#e6e6e6")

    st.pyplot(fig, use_container_width=True)

# ===================== MÉTRICAS POR PERFIL =====================
st.subheader("Métricas no preço atual")
col_perfis = st.columns(3)
for i, (nome, q, E, R, cor) in enumerate(linhas_info):
    with col_perfis[i]:
        with st.container(border=True):
            st.markdown(f"### {nome}")
            st.markdown(f"- **Quantidade (Q):** {int(q):,}".replace(",", "."))
            st.markdown(f"- **Elasticidade (E):** {'—' if np.isnan(E) else f'{E:.2f}'}  \n"
                        f"  **Classificação:** {classifica(E)}")
            st.markdown(f"- **Receita (R = P×Q):** R$ {int(R):,}".replace(",", "."))

# ===================== TABELA + DOWNLOAD =====================
st.subheader("Tabela resumo (preço atual)")
linhas_tabela = []
for nome, q, E, R, _ in linhas_info:
    linhas_tabela.append({
        "Perfil": nome,
        "Quantidade (Q)": int(q),
        "Elasticidade (E)": "-" if np.isnan(E) else f"{E:.2f}",
        "Classificação": classifica(E),
        "Receita (R$)": int(R)
    })
df = pd.DataFrame(linhas_tabela)
st.dataframe(df, use_container_width=True)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Baixar CSV do resumo", csv, file_name="resumo_elasticidade.csv", mime="text/csv")

# ===================== EXEMPLOS PARA NARRATIVA =====================
with st.expander("Exemplos de interpretação (narrativa rápida)"):
    st.markdown(
        f"""
- **Estudante** tende a ter **orçamento restrito** e alta sensibilidade a preço (b maior). Produtos típicos na faixa R$ 1.000–3.000: 
  **notebook de entrada**, **cadeira gamer/estudo**, **smartphone intermediário**.
- **Família** busca **custo-benefício** com compras planejadas; sensibilidade moderada. Exemplos: **micro-ondas**, **purificador**, **TV básica**.
- **Empresa** tem foco em **produtividade/ROI** e menor sensibilidade unitária; compra com critério técnico. Exemplos: **cadeira ergonômica**, **impressora**, **licenças de software**.
- Use o **cenário** (sidebar) para simular choques: renda, crédito e recessão alteram **a** (nível de demanda).
"""
    )

# ===================== IA GENERATIVA (PARA AVALIAÇÃO) =====================
with st.expander("Como usamos IA generativa neste artefato"):
    st.markdown("""
- **ChatGPT** ajudou a: (i) estruturar a aplicação em **Streamlit**, (ii) escrever funções vetorizadas com **NumPy** para
  **quantidade** e **elasticidade pontual**, (iii) organizar **layout** (cards, gráfico, tabela) e (iv) documentar o raciocínio econômico.
- Iteramos prompts para:
  1) calibrar **a** e **b** por persona (Estudante, Família, Empresa),  
  2) adicionar **cenários** (choques de demanda) e  
  3) deixar o **gráfico legível em projetor** (tema escuro, contraste).
- Resultado: um **artefato interativo** que traduz elasticidade-preço em prática, com **cálculo consistente** e **narrativa** para a apresentação oral.
""")
