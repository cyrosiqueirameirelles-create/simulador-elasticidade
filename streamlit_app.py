import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from io import BytesIO
from matplotlib.ticker import FuncFormatter

# ===========================
# CONFIG E PALETA
# ===========================
st.set_page_config(page_title="Elasticidade – Perfis (R$1.000 a R$3.000)", layout="wide")

COL_BG_DARK   = "#0f1116"
COL_AX_DARK   = "#0f1116"
COL_GRID      = "#2a3146"
COL_LABEL     = "#cfd6e6"
COL_TITLE     = "#ffffff"
COL_PRICE     = "#c33d3d"

COL_EST = "#f7b500"  # Estudante
COL_EMP = "#3aa0ff"  # Empresa
COL_FAM = "#38d39f"  # Família

def fmt_moeda(x, pos):
    return f"R${int(x):,}".replace(",", ".")

# ===========================
# CABEÇALHO
# ===========================
st.title("📊 Elasticidade por Perfil – Faixa de Preços Alta (R$ 1.000 a R$ 3.000)")
st.markdown(
    """
**Propósito.** Este painel ilustra como diferentes **perfis de consumidores** reagem a variações de **preços elevados**.
Usamos uma função com **preço máximo tolerado (P\*)**, onde cada perfil deixa de comprar acima do seu P\*:

- **Estudante**: maior sensibilidade → **P\*** mais baixo (desiste primeiro)  
- **Família**: sensibilidade intermediária → **P\*** mediano  
- **Empresa**: menor sensibilidade → **P\*** mais alto (desiste por último)

Para um preço corrente \(P\), mostramos a **quantidade demandada \(Q\)** e a **elasticidade pontual** de cada perfil.
"""
)

# ===========================
# CONTROLES
# ===========================
st.sidebar.header("⚙️ Parâmetros do experimento")

preco = st.sidebar.slider("💰 Preço do produto (R$)", min_value=1000, max_value=3000, value=1800, step=50)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Perfis e preços máximos tolerados (P*)")

with st.sidebar.expander("👩‍🎓 Estudante (sensível) – desiste cedo", True):
    a_est = st.number_input("Q(0)=a – Estudante", min_value=10.0, value=80.0, step=5.0)
    pstar_est = st.number_input("P* (máximo tolerado) – Estudante (R$)", min_value=1000, max_value=3000, value=1200, step=50)

with st.sidebar.expander("👨‍👩‍👧 Família (médio) – desiste depois", True):
    a_fam = st.number_input("Q(0)=a – Família", min_value=10.0, value=70.0, step=5.0)
    pstar_fam = st.number_input("P* (máximo tolerado) – Família (R$)", min_value=1000, max_value=3000, value=2200, step=50)

with st.sidebar.expander("🏢 Empresa (pouco sensível) – desiste por último", True):
    a_emp = st.number_input("Q(0)=a – Empresa", min_value=10.0, value=65.0, step=5.0)
    pstar_emp = st.number_input("P* (máximo tolerado) – Empresa (R$)", min_value=1000, max_value=3000, value=3000, step=50)

def reset():
    st.session_state["a_est"], st.session_state["pstar_est"] = 80.0, 1200
    st.session_state["a_fam"], st.session_state["pstar_fam"] = 70.0, 2200
    st.session_state["a_emp"], st.session_state["pstar_emp"] = 65.0, 3000

if st.sidebar.button("↺ Restaurar padrões"):
    reset()
    st.experimental_rerun()

# ===========================
# MODELO E MÉTRICAS
# ===========================
def Q_linear_a_pstar(a, pstar, p):
    """
    Q(P) = a * (1 - P/P*), para P <= P*; 0 para P > P*.
    Robusta a escalar (float/int) e array.
    """
    p_arr = np.asarray(p, dtype=float)
    q = a * (1 - p_arr / pstar)
    if p_arr.ndim == 0:  # escalar
        return float(max(0.0, q))
    # array
    q[p_arr > pstar] = 0.0
    q = np.maximum(0.0, q)
    return q

def elasticidade_pontual(a, pstar, p):
    """
    Para Q = a * (1 - P/P*), dQ/dP = -a/P*
    E = (dQ/dP)*(P/Q) = (-a/P*) * (P / Q)
    Retorna None quando Q=0.
    """
    q = Q_linear_a_pstar(a, pstar, p)
    # garantir escalar para o teste
    q_val = float(q) if np.ndim(q) == 0 else float(np.asarray(q))
    if q_val <= 0:
        return None
    return (-a / pstar) * (p / q_val)

perfis = {
    "Estudante": {"a": a_est, "pstar": pstar_est, "cor": COL_EST},
    "Família":   {"a": a_fam, "pstar": pstar_fam, "cor": COL_FAM},
    "Empresa":   {"a": a_emp, "pstar": pstar_emp, "cor": COL_EMP},
}

linhas = []
for nome, cfg in perfis.items():
    a, pstar, cor = cfg["a"], cfg["pstar"], cfg["cor"]
    q_atual = Q_linear_a_pstar(a, pstar, preco)   # agora funciona com escalar
    E = elasticidade_pontual(a, pstar, preco)
    linhas.append((nome, a, pstar, float(q_atual), E, cor))

def classif(E):
    if E is None: return "sem demanda"
    v = abs(E)
    if v > 1: return "elástica (>1)"
    if v < 1: return "inelástica (<1)"
    return "unitária (=1)"

# ===========================
# CARDS
# ===========================
st.markdown("### Resultados no preço atual")
c1, c2, c3 = st.columns(3)
for col, (nome, a, pstar, q, E, cor) in zip([c1, c2, c3], linhas):
    with col:
        st.markdown(
            f"""
<div style="background:#f7f9fc;border:1px solid #e5eaf1;border-radius:14px;padding:14px 16px;">
  <div style="font-weight:700;color:#111827;font-size:16px;">{nome}</div>
  <div style="display:flex;gap:18px;margin-top:8px;flex-wrap:wrap;">
    <div>
      <div style="font-size:12px;color:#6b7280;">Q(0)=a</div>
      <div style="font-size:18px;font-weight:700;color:#111827;">{a:.0f}</div>
    </div>
    <div>
      <div style="font-size:12px;color:#6b7280;">P*</div>
      <div style="font-size:18px;font-weight:700;color:#111827;">R${int(pstar):,}</div>
    </div>
    <div>
      <div style="font-size:12px;color:#6b7280;">Q no preço</div>
      <div style="font-size:22px;font-weight:700;color:#111827;">{q:.1f}</div>
    </div>
    <div>
      <div style="font-size:12px;color:#6b7280;">|E|</div>
      <div style="font-size:18px;font-weight:700;color:#111827;">{"-" if E is None else f"{abs(E):.2f}"}</div>
    </div>
    <div>
      <div style="font-size:12px;color:#6b7280;">Classe</div>
      <div style="font-size:14px;font-weight:700;color:{cor};">{classif(E)}</div>
    </div>
  </div>
</div>
""".replace(",", "."),
            unsafe_allow_html=True
        )

st.info(f"Preço selecionado: **R$ {preco:,}**".replace(",", "."))

# ===========================
# GRÁFICO
# ===========================
P = np.linspace(1000, 3000, 1200)

fig, ax = plt.subplots(figsize=(10, 5.6))
fig.patch.set_facecolor(COL_BG_DARK)
ax.set_facecolor(COL_AX_DARK)

for (nome, a, pstar, q_atual, E, cor) in linhas:
    q_curve = Q_linear_a_pstar(a, pstar, P)
    mask = P <= pstar                       # parte viável apenas
    ax.plot(P[mask], q_curve[mask], color=cor, linewidth=2.6, label=f"{nome}")
    # intercepto no P* (zeração)
    ax.scatter([pstar], [0], color=cor, s=40, zorder=4)
    ax.text(pstar, 0 + a*0.04, f"P*={int(pstar)}", color=COL_LABEL, ha="center",
            bbox=dict(facecolor=COL_BG_DARK, alpha=0.65, edgecolor="none", pad=1.5), fontsize=10)
    # ponto no preço atual
    ax.scatter([preco], [q_atual], color=cor, s=70, zorder=5)
    ax.text(preco, q_atual + a*0.04, f"{q_atual:.1f}", color=COL_LABEL, ha="center",
            bbox=dict(facecolor=COL_BG_DARK, alpha=0.65, edgecolor="none", pad=1.5), fontsize=10)

# linha do preço atual
ax.axvline(preco, color=COL_PRICE, linestyle="--", linewidth=1.5, label="Preço selecionado")

# estilo
ax.grid(color=COL_GRID, linestyle=":", linewidth=0.8, alpha=0.7)
ax.set_xlabel("Preço (R$)", color=COL_LABEL)
ax.set_ylabel("Quantidade Demandada", color=COL_LABEL)
ax.set_title("Curvas por Perfil (modelo com preço máximo tolerado P*)", color=COL_TITLE, pad=10, fontsize=18)
ax.tick_params(colors=COL_LABEL)
ax.xaxis.set_major_formatter(FuncFormatter(fmt_moeda))

ax.set_xlim(1000, 3000)
ax.set_ylim(0, max(a_est, a_fam, a_emp) * 1.22)

leg = ax.legend(facecolor="#1a1f2e", edgecolor="#2a3146")
for t in leg.get_texts():
    t.set_color("#e6e6e6")

st.pyplot(fig, use_container_width=True)

# download do gráfico
buf = BytesIO()
fig.savefig(buf, format="png", dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
st.download_button("⤓ Baixar gráfico (PNG)", data=buf.getvalue(),
                   file_name="curvas_perfis_alta_faixa.png", mime="image/png")

# ===========================
# TABELA
# ===========================
st.markdown("### Tabela (parâmetros e resultados no preço atual)")
df = pd.DataFrame([{
    "Perfil": nome,
    "Q(0)=a": int(a),
    "P* (R$)": int(pstar),
    "Q no preço": round(q, 1),
    "Elasticidade (|E|)": "-" if E is None else f"{abs(E):.2f}",
    "Classificação": classif(E),
} for (nome, a, pstar, q, E, _) in linhas])
st.dataframe(df, use_container_width=True)

# ===========================
# NOTA METODOLÓGICA
# ===========================
with st.expander("Nota metodológica"):
    st.markdown(
        """
- **Formulação:** \( Q(P) = a \cdot (1 - P/P^*) \) até \(P = P^*\); acima disso, \(Q=0\).
- **Interpretação:** \(P^*\) é o **limite de tolerância a preço** do perfil (quanto maior, menos sensível).
- **Elasticidade:** exibimos a **pontual** no preço atual \(P\) (guia para decisões de preço por segmento).
"""
    )
