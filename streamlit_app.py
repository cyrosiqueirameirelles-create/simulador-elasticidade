import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Simulador de Elasticidade-Preço", layout="wide")

st.title("📊 Simulador de Elasticidade-Preço da Demanda (3 perfis)")
st.write(
    "Ajuste o **preço** e a **angulação das curvas** (parâmetros de \(Q=a-bP\)) para Estudante, Empresa e Família. "
    "Veja em tempo real as **quantidades** e **elasticidades**."
)

# -------------------- CONTROLES GERAIS --------------------
preco = st.slider("💰 Preço do produto (R$)", min_value=10, max_value=100, value=25, step=1)

# Defaults “bonitos” (ângulos bem diferentes)
defaults = {
    "Estudante": {"a": 75.0, "b": 3.00, "cor": "#f7b500"},  # amarelo (mais elástica)
    "Empresa":   {"a": 65.0, "b": 0.55, "cor": "#3aa0ff"},  # azul (inelástica)
    "Família":   {"a": 70.0, "b": 1.50, "cor": "#38d39f"},  # verde (médio)
}

st.markdown("#### Ajuste a angulação das curvas (intercepto **a** e inclinação **b**)")
c1, c2, c3 = st.columns(3)

with c1:
    st.caption("**Estudante**")
    a_est = st.number_input("a (Q quando P=0)", value=defaults["Estudante"]["a"], step=1.0, key="a_est")
    b_est = st.number_input("b (inclinação)", value=defaults["Estudante"]["b"], step=0.05, min_value=0.05, key="b_est")

with c2:
    st.caption("**Empresa**")
    a_emp = st.number_input("a (Q quando P=0)", value=defaults["Empresa"]["a"], step=1.0, key="a_emp")
    b_emp = st.number_input("b (inclinação)", value=defaults["Empresa"]["b"], step=0.05, min_value=0.05, key="b_emp")

with c3:
    st.caption("**Família**")
    a_fam = st.number_input("a (Q quando P=0)", value=defaults["Família"]["a"], step=1.0, key="a_fam")
    b_fam = st.number_input("b (inclinação)", value=defaults["Família"]["b"], step=0.05, min_value=0.05, key="b_fam")

# Botão para resetar para os defaults
if st.button("↺ Restaurar ângulos padrão"):
    st.session_state["a_est"] = defaults["Estudante"]["a"]
    st.session_state["b_est"] = defaults["Estudante"]["b"]
    st.session_state["a_emp"] = defaults["Empresa"]["a"]
    st.session_state["b_emp"] = defaults["Empresa"]["b"]
    st.session_state["a_fam"] = defaults["Família"]["a"]
    st.session_state["b_fam"] = defaults["Família"]["b"]
    st.experimental_rerun()

# -------------------- FUNÇÕES --------------------
def Q(a, b, p):  # quantidade
    return max(0.0, a - b * p)

def E_pontual(a, b, p):
    q = Q(a, b, p)
    if q == 0:
        return None
    return -b * (p / q)  # (dQ/dP)*(P/Q) = (-b)*(P/Q)

def classif(E):
    if E is None:
        return "sem demanda"
    x = abs(E)
    if x > 1: return "elástica (>1)"
    if x < 1: return "inelástica (<1)"
    return "unitária (=1)"

# -------------------- DADOS --------------------
perfis = {
    "Estudante": {"a": a_est, "b": b_est, "cor": defaults["Estudante"]["cor"]},
    "Empresa":   {"a": a_emp, "b": b_emp, "cor": defaults["Empresa"]["cor"]},
    "Família":   {"a": a_fam, "b": b_fam, "cor": defaults["Família"]["cor"]},
}

precos = list(range(10, 101))
series = {}
linhas = []
for nome, cfg in perfis.items():
    a, b, cor = cfg["a"], cfg["b"], cfg["cor"]
    qs = [Q(a, b, p) for p in precos]
    q_atual = Q(a, b, preco)
    e_atual = E_pontual(a, b, preco)
    series[nome] = {"precos": precos, "qs": qs, "q_atual": q_atual, "E": e_atual, "cor": cor}
    linhas.append((nome, q_atual, e_atual, cor, a, b))

# Resumo didático com |E|
resumo = " • ".join(
    [f"**{n}**: Q = **{int(q)}** | |E| = {('-' if E is None else f'{abs(E):.2f}')} ( {classif(E)} )"
     for n, q, E, *_ in linhas]
)
st.info(f"Preço selecionado: **R$ {preco}**  |  {resumo}")

# -------------------- GRÁFICO (tema escuro) --------------------
fig, ax = plt.subplots(figsize=(9, 5))
fig.patch.set_facecolor("#0f1116")
ax.set_facecolor("#0f1116")

for nome, dados in series.items():
    ax.plot(dados["precos"], dados["qs"], label=f"Demanda – {nome}",
            color=dados["cor"], linewidth=2.2)
    ax.scatter([preco], [dados["q_atual"]], color=dados["cor"], s=60, zorder=5)

ax.axvline(preco, color="#c33d3d", linestyle="--", linewidth=1.4, label="Preço selecionado")
ax.grid(color="#2a3146", linestyle=":", linewidth=0.8, alpha=0.7)
ax.set_xlabel("Preço (R$)", color="#cfd6e6")
ax.set_ylabel("Quantidade Demandada", color="#cfd6e6")
ax.set_title("Curvas de Demanda por Perfil (ajuste \(a\) e \(b\))", color="#ffffff", pad=10, fontsize=18)
ax.tick_params(colors="#cfd6e6")
leg = ax.legend(facecolor="#1a1f2e", edgecolor="#2a3146")
for t in leg.get_texts(): t.set_color("#e6e6e6")

st.pyplot(fig, use_container_width=True)

# -------------------- TABELA --------------------
st.subheader("Quantidades, elasticidades e parâmetros no preço atual")
df = pd.DataFrame([{
    "Perfil": n,
    "Quantidade": int(q),
    "Elasticidade (|E|)": "-" if E is None else f"{abs(E):.2f}",
    "Classificação": classif(E),
    "a": round(a, 2),
    "b (inclinação)": round(b, 2),
} for n, q, E, _, a, b in linhas])
st.dataframe(df, use_container_width=True)

with st.expander("Como usamos IA generativa neste artefato"):
    st.markdown("""
- **ChatGPT** gerou o código base em **Python + Streamlit**, os cálculos de **elasticidade pontual** e o layout.
- Iteramos prompts para adicionar **ajuste de angulação (a e b)** ao vivo, mostrar **todas as curvas** juntas e exibir **resumo e tabela** automáticos.
- Resultado: um **artefato interativo** que conecta teoria (elasticidade) com prática (segmentos com sensibilidades diferentes).
""")
