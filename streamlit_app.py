import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from io import BytesIO
from matplotlib.ticker import FuncFormatter

# ===========================
# Config & paleta
# ===========================
st.set_page_config(page_title="Elasticidade por Perfil (R$ 1.000–3.000)", layout="wide")

COL_BG_DARK   = "#0f1116"
COL_AX_DARK   = "#0f1116"
COL_GRID      = "#283046"
COL_LABEL     = "#dbe2f1"
COL_TITLE     = "#ffffff"
COL_PRICE     = "#ff6b6b"

COL_EST = "#f7b500"  # estudante
COL_FAM = "#38d39f"  # família
COL_EMP = "#3aa0ff"  # empresa

# tons suaves (faixas)
BAND_EST = "#f7b5001a"
BAND_FAM = "#38d39f1a"
BAND_EMP = "#3aa0ff1a"

def fmt_moeda(x, pos):
    return f"R${int(x):,}".replace(",", ".")

# ===========================
# Cabeçalho
# ===========================
st.title("📊 Elasticidade por Perfil — Faixa Alta de Preços (R$ 1.000 a R$ 3.000)")
st.markdown("""
**Leitura rápida.** Cada perfil tem um **preço máximo tolerado (P\*)**:
- **Estudante** desiste primeiro (P\* mais baixo),
- **Família** aguenta mais (P\* intermediário),
- **Empresa** é a menos sensível (P\* mais alto).

O gráfico mostra **apenas** a parte onde cada perfil **ainda compra**. Acima de P\*, a quantidade vira **0**.
""")

# ===========================
# Controles (sidebar)
# ===========================
st.sidebar.header("⚙️ Parâmetros do experimento")

preco = st.sidebar.slider("💰 Preço do produto (R$)", 1000, 3000, 1800, 50)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Perfis e seus P* (preço máximo tolerado)")

with st.sidebar.expander("👩‍🎓 Estudante (sensível) — desiste cedo", True):
    a_est   = st.number_input("Q(0)=a — Estudante", value=80.0, min_value=10.0, step=5.0)
    pstar_est = st.number_input("P* — Estudante (R$)", value=1200, min_value=1000, max_value=3000, step=50)

with st.sidebar.expander("👨‍👩‍👧 Família (médio) — desiste depois", True):
    a_fam   = st.number_input("Q(0)=a — Família", value=70.0, min_value=10.0, step=5.0)
    pstar_fam = st.number_input("P* — Família (R$)", value=2200, min_value=1000, max_value=3000, step=50)

with st.sidebar.expander("🏢 Empresa (pouco sensível) — desiste por último", True):
    a_emp   = st.number_input("Q(0)=a — Empresa", value=65.0, min_value=10.0, step=5.0)
    pstar_emp = st.number_input("P* — Empresa (R$)", value=3000, min_value=1000, max_value=3000, step=50)

def Q_a_pstar(a, pstar, p):
    """Q(P) = a*(1 - P/P*) para P<=P*; 0 acima de P*."""
    p = np.asarray(p, dtype=float)
    q = a * (1 - p / pstar)
    q[p > pstar] = 0.0
    return np.maximum(0.0, q)

def E_a_pstar(a, pstar, p):
    """Elasticidade pontual de Q = a(1 - P/P*): dQ/dP = -a/P*; E = (-a/P*)*(P/Q)."""
    q = float(Q_a_pstar(a, pstar, p))
    if q <= 0:
        return None
    return (-a / pstar) * (p / q)

perfis = [
    ("Estudante", a_est, pstar_est, COL_EST, BAND_EST),
    ("Família",   a_fam, pstar_fam, COL_FAM, BAND_FAM),
    ("Empresa",   a_emp, pstar_emp, COL_EMP, BAND_EMP),
]

# cards
st.markdown("### Resultados no preço atual")
c1, c2, c3 = st.columns(3)
for col, (nome, a, pstar, cor, _) in zip([c1,c2,c3], perfis):
    q = float(Q_a_pstar(a, pstar, preco))
    E = E_a_pstar(a, pstar, preco)
    cls = "sem demanda" if E is None else ("elástica (>1)" if abs(E) > 1 else ("unitária (=1)" if abs(E)==1 else "inelástica (<1)"))
    col.markdown(
f"""
<div style="background:#f7f9fc;border:1px solid #e5eaf1;border-radius:14px;padding:14px 16px;">
  <div style="font-weight:700;color:#111827;font-size:16px;">{nome}</div>
  <div style="display:flex;gap:18px;margin-top:8px;flex-wrap:wrap;">
    <div><div style="font-size:12px;color:#6b7280;">Q(0)=a</div>
    <div style="font-size:18px;font-weight:700;color:#111827;">{a:.0f}</div></div>

    <div><div style="font-size:12px;color:#6b7280;">P*</div>
    <div style="font-size:18px;font-weight:700;color:#111827;">R${pstar:,}</div></div>

    <div><div style="font-size:12px;color:#6b7280;">Q no preço</div>
    <div style="font-size:22px;font-weight:700;color:#111827;">{q:.1f}</div></div>

    <div><div style="font-size:12px;color:#6b7280;">|E|</div>
    <div style="font-size:18px;font-weight:700;color:#111827;">{"-" if E is None else f"{abs(E):.2f}"}</div></div>

    <div><div style="font-size:12px;color:#6b7280;">Classe</div>
    <div style="font-size:14px;font-weight:700;color:{cor};">{cls}</div></div>
  </div>
</div>
""".replace(",", "."), unsafe_allow_html=True)

st.info(f"Preço selecionado: **R$ {preco:,}**".replace(",", "."))

# ===========================
# GRÁFICO – versão didática com faixas
# ===========================
P = np.linspace(1000, 3000, 1200)

# ordenar P* para criar bandas na ordem correta
sorted_pstars = sorted([(pstar_est, "Estudante", BAND_EST),
                        (pstar_fam, "Família",   BAND_FAM),
                        (pstar_emp, "Empresa",   BAND_EMP)],
                       key=lambda x: x[0])

fig, ax = plt.subplots(figsize=(10.5, 6.2))
fig.patch.set_facecolor(COL_BG_DARK)
ax.set_facecolor(COL_AX_DARK)

# 1) FAIXAS DE CONTEXTO (onde cada perfil ainda compra)
x_left = 1000
for pstar, label, band_col in sorted_pstars:
    ax.axvspan(x_left, pstar, color=band_col, ymin=0, ymax=1)
    # rótulo da faixa
    cx = (x_left + pstar) / 2
    ax.text(cx, 0.95, f"Até aqui {label} compra",
            color=COL_LABEL, ha="center", va="top", fontsize=10,
            bbox=dict(facecolor="#00000055", edgecolor="none", pad=2))
    x_left = pstar
# após maior P*, “ninguém compra”
if x_left < 3000:
    ax.axvspan(x_left, 3000, color="#ff6b6b10", ymin=0, ymax=1)
    cx = (x_left + 3000) / 2
    ax.text(cx, 0.95, "Acima do maior P*: ninguém compra",
            color="#ffb3b3", ha="center", va="top", fontsize=10,
            bbox=dict(facecolor="#00000055", edgecolor="none", pad=2))

# 2) CURVAS (somente trecho com Q>0)
for nome, a, pstar, cor, _band in perfis:
    q_curve = Q_a_pstar(a, pstar, P)
    mask = P <= pstar
    ax.plot(P[mask], q_curve[mask], color=cor, linewidth=3, label=nome)
    # intercepto em P*
    ax.scatter([pstar], [0], color=cor, s=50, zorder=5)
    ax.text(pstar, max(a*0.05, 1), f"P*={pstar}",
            color=COL_LABEL, ha="center", va="bottom", fontsize=10,
            bbox=dict(facecolor="#00000070", edgecolor="none", pad=2))

# 3) PONTO DO PREÇO ATUAL
for nome, a, pstar, cor, _ in perfis:
    q = float(Q_a_pstar(a, pstar, preco))
    ax.scatter([preco], [q], color=cor, s=110, edgecolor="white", linewidth=1.2, zorder=6)
    ax.text(preco, q + max(a*0.05, 1.5), f"{q:.1f}",
            color=COL_LABEL, ha="center", va="bottom", fontsize=10,
            bbox=dict(facecolor="#00000070", edgecolor="none", pad=2))

# linha vertical do preço atual + label
ax.axvline(preco, color=COL_PRICE, linestyle=(0,(6,6)), linewidth=2.2)
ax.text(preco, ax.get_ylim()[1]*0.88, "Preço atual",
        color="#ffd6d6", ha="center", va="bottom", fontsize=11,
        bbox=dict(facecolor="#55000080", edgecolor="none", pad=2))

# 4) estilo geral
ax.grid(color=COL_GRID, linestyle=":", linewidth=0.9, alpha=0.7)
ax.set_xlim(1000, 3000)
ax.set_ylim(0, max(a_est, a_fam, a_emp)*1.25)

ax.set_xlabel("Preço (R$)", color=COL_LABEL, labelpad=8)
ax.set_ylabel("Quantidade Demandada", color=COL_LABEL, labelpad=8)
ax.set_title("Curvas por Perfil (com P* e zonas de compra por segmento)", color=COL_TITLE, pad=12, fontsize=18)
ax.tick_params(colors=COL_LABEL)
ax.xaxis.set_major_formatter(FuncFormatter(fmt_moeda))

leg = ax.legend(facecolor="#1a1f2e", edgecolor="#2a3146")
for t in leg.get_texts():
    t.set_color("#e6e6e6")

st.pyplot(fig, use_container_width=True)

# download
buf = BytesIO()
fig.savefig(buf, format="png", dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
st.download_button("⤓ Baixar gráfico (PNG)", data=buf.getvalue(),
                   file_name="perfis_faixa_alta_com_bandas.png", mime="image/png")

# ===========================
# Tabela
# ===========================
st.markdown("### Tabela — parâmetros e resultados no preço atual")
rows = []
for nome, a, pstar, cor, _ in perfis:
    q = float(Q_a_pstar(a, pstar, preco))
    E = E_a_pstar(a, pstar, preco)
    cls = "sem demanda" if E is None else ("elástica (>1)" if abs(E) > 1 else ("unitária (=1)" if abs(E)==1 else "inelástica (<1)"))
    rows.append({
        "Perfil": nome,
        "Q(0)=a": int(a),
        "P* (R$)": int(pstar),
        "Q no preço": round(q, 1),
        "Elasticidade (|E|)": "-" if E is None else f"{abs(E):.2f}",
        "Classificação": cls
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ===========================
# Nota metodológica curta
# ===========================
with st.expander("Nota metodológica (resumo)"):
    st.markdown("""
- Modelo: \(Q(P) = a\,(1 - P/P^*)\) para \(P \le P^*\); acima disso \(Q=0\).
- \(P^*\) é o **limite de tolerância a preço** do perfil (quanto maior, **menos sensível**).
- Elasticidade exibida é a **pontual** no preço atual \(P\).
- Zonas coloridas no gráfico indicam **onde cada perfil ainda compra**.
""")
