import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Simulador de Elasticidade-Preço", layout="wide")

# Cores (gráfico dark + UI clara)
COL_BG_DARK   = "#0f1116"
COL_AX_DARK   = "#0f1116"
COL_GRID      = "#2a3146"
COL_LABEL     = "#cfd6e6"
COL_TITLE     = "#ffffff"

COL_EST = "#f7b500"  # Estudante
COL_EMP = "#3aa0ff"  # Empresa
COL_FAM = "#38d39f"  # Família

# ------------------ TÍTULO ------------------
st.title("📊 Simulador de Elasticidade-Preço da Demanda")
st.write("Ajuste o **preço** e os parâmetros \(Q=a-bP\) na barra lateral. A visualização mostra **apenas o preço atual**, sem curvas completas.")

# ------------------ SIDEBAR ------------------
st.sidebar.header("⚙️ Controles")

preco = st.sidebar.slider("💰 Preço do produto (R$)", min_value=10, max_value=100, value=25, step=1)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Parâmetros das funções (Q = a − b·P)")

with st.sidebar.expander("👩‍🎓 Estudante (mais sensível)", True):
    a_est = st.number_input("a (Q quando P=0) – Estudante", value=75.0, step=1.0, key="a_est")
    b_est = st.number_input("b (inclinação) – Estudante",  value=3.00, step=0.05, min_value=0.05, key="b_est")

with st.sidebar.expander("🏢 Empresa (menos sensível)", True):
    a_emp = st.number_input("a (Q quando P=0) – Empresa", value=65.0, step=1.0, key="a_emp")
    b_emp = st.number_input("b (inclinação) – Empresa",  value=0.55, step=0.05, min_value=0.05, key="b_emp")

with st.sidebar.expander("👨‍👩‍👧 Família (sensibilidade média)", True):
    a_fam = st.number_input("a (Q quando P=0) – Família", value=70.0, step=1.0, key="a_fam")
    b_fam = st.number_input("b (inclinação) – Família",  value=1.50, step=0.05, min_value=0.05, key="b_fam")

def reset():
    st.session_state.a_est, st.session_state.b_est = 75.0, 3.00
    st.session_state.a_emp, st.session_state.b_emp = 65.0, 0.55
    st.session_state.a_fam, st.session_state.b_fam = 70.0, 1.50

if st.sidebar.button("↺ Restaurar padrões"):
    reset()
    st.experimental_rerun()

# ------------------ FUNÇÕES ------------------
def Q(a: float, b: float, p: float) -> float:
    return max(0.0, a - b * p)

def E_pontual(a: float, b: float, p: float):
    """Elasticidade-preço pontual: E = (dQ/dP)*(P/Q) = (-b)*(P/Q)"""
    q = Q(a, b, p)
    if q == 0:
        return None
    return -b * (p / q)

def classif(E):
    if E is None:
        return "sem demanda"
    x = abs(E)
    if x > 1: return "elástica (>1)"
    if x < 1: return "inelástica (<1)"
    return "unitária (=1)"

# ------------------ DADOS NO PREÇO ATUAL ------------------
perfis = {
    "Estudante": {"a": a_est, "b": b_est, "cor": COL_EST},
    "Empresa":   {"a": a_emp, "b": b_emp, "cor": COL_EMP},
    "Família":   {"a": a_fam, "b": b_fam, "cor": COL_FAM},
}

linhas = []
for nome, cfg in perfis.items():
    a, b, cor = cfg["a"], cfg["b"], cfg["cor"]
    q = Q(a, b, preco)
    E = E_pontual(a, b, preco)
    linhas.append((nome, q, E, cor, a, b))

# ------------------ CARDS (DESTAQUES) ------------------
st.markdown("### Resultados no preço atual")
c1, c2, c3 = st.columns(3)
cards = [c1, c2, c3]
for col, (nome, q, E, cor, a, b) in zip(cards, linhas):
    with col:
        box = f"""
        <div style="
            background:#f7f9fc; border:1px solid #e5eaf1; border-radius:14px;
            padding:14px 16px;">
            <div style="font-weight:700; color:#111827; font-size:16px;">{nome}</div>
            <div style="display:flex; gap:18px; margin-top:8px;">
                <div>
                    <div style="font-size:12px; color:#6b7280;">Quantidade</div>
                    <div style="font-size:22px; font-weight:700; color:#111827;">{int(q)}</div>
                </div>
                <div>
                    <div style="font-size:12px; color:#6b7280;">|E|</div>
                    <div style="font-size:22px; font-weight:700; color:#111827;">{('-' if E is None else f'{abs(E):.2f}')}</div>
                </div>
                <div>
                    <div style="font-size:12px; color:#6b7280;">Classe</div>
                    <div style="font-size:14px; font-weight:700; color:{cor};">{classif(E)}</div>
                </div>
            </div>
        </div>
        """
        st.markdown(box, unsafe_allow_html=True)

st.info(f"Preço selecionado: **R$ {preco}**")

# ------------------ GRÁFICO DE BARRAS (SEM CURVA) ------------------
labels = [n for n, *_ in linhas]
qs = [q for _, q, *_ in linhas]
colors = [c for *_, c, __, ___ in linhas]

fig, ax = plt.subplots(figsize=(9.5, 5.2))
fig.patch.set_facecolor(COL_BG_DARK)
ax.set_facecolor(COL_AX_DARK)

bars = ax.bar(labels, qs, color=colors)
ax.grid(axis="y", color=COL_GRID, linestyle=":", linewidth=0.8, alpha=0.7)

# valores acima das barras
for rect in bars:
    height = rect.get_height()
    ax.text(rect.get_x() + rect.get_width()/2., height + max(qs)*0.02 if max(qs) > 0 else 0.5,
            f"{int(height)}", ha='center', va='bottom', color=COL_LABEL, fontsize=11)

ax.set_ylabel("Quantidade Demandada", color=COL_LABEL)
ax.set_title("Comparação de Quantidade por Perfil (no preço atual)", color=COL_TITLE, pad=10, fontsize=18)
ax.tick_params(colors=COL_LABEL)
# eixo x labels brancos:
for tick in ax.get_xticklabels():
    tick.set_color(COL_LABEL)

st.pyplot(fig, use_container_width=True)

# ------------------ DOWNLOAD DO GRÁFICO ------------------
buf = BytesIO()
fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
st.download_button("⤓ Baixar gráfico (PNG)", data=buf.getvalue(),
                   file_name="quantidade_por_perfil.png", mime="image/png")

# ------------------ TABELA ------------------
st.markdown("### Tabela (quantidades, elasticidades e parâmetros)")
df = pd.DataFrame([{
    "Perfil": n,
    "Quantidade": int(q),
    "Elasticidade (|E|)": "-" if E is None else f"{abs(E):.2f}",
    "Classificação": classif(E),
    "a": round(a, 2),
    "b (inclinação)": round(b, 2),
} for n, q, E, c, a, b in linhas])
st.dataframe(df, use_container_width=True)

# ------------------ EXPLICANDO A IA ------------------
with st.expander("Como usamos IA generativa neste artefato"):
    st.markdown("""
- **ChatGPT** gerou e refinou o código em **Python + Streamlit**, incluindo o cálculo de **elasticidade pontual** e a organização visual.
- Iteramos prompts para: colocar controles na **barra lateral**, criar **cards** de destaque e trocar a visualização para **barras (sem curvas)**.
- O app final é um **artefato interativo** que conecta teoria (elasticidade) a um cenário pontual de preço.
""")
