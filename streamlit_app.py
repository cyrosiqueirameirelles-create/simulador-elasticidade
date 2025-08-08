import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from io import BytesIO

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Simulador de Elasticidade-Preço", layout="wide")

# Cores (gráfico dark + UI clara)
COL_BG_DARK   = "#0f1116"
COL_AX_DARK   = "#0f1116"
COL_GRID      = "#2a3146"
COL_LABEL     = "#cfd6e6"
COL_TITLE     = "#ffffff"
COL_PRICE     = "#c33d3d"

COL_EST = "#f7b500"  # Estudante
COL_EMP = "#3aa0ff"  # Empresa
COL_FAM = "#38d39f"  # Família

# ------------------ TÍTULO ------------------
st.title("📊 Simulador de Elasticidade-Preço da Demanda")
st.write("Ajuste o **preço** e os parâmetros \(Q=a-bP\) na barra lateral. O gráfico mostra as **curvas precisas** por perfil.")

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
def Q(a: float, b: float, p):
    return np.maximum(0.0, a - b * p)  # aceita escalar ou array

def Q_raw(a: float, b: float, p):
    return a - b * p  # sem truncar (pra desenhar trecho inviável)

def E_pontual(a: float, b: float, p: float):
    q = max(0.0, a - b * p)
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

def choke_price(a, b):
    return a / b  # P* (Q=0)

# ------------------ DADOS NO PREÇO ATUAL ------------------
perfis = {
    "Estudante": {"a": a_est, "b": b_est, "cor": COL_EST},
    "Empresa":   {"a": a_emp, "b": b_emp, "cor": COL_EMP},
    "Família":   {"a": a_fam, "b": b_fam, "cor": COL_FAM},
}

linhas = []
for nome, cfg in perfis.items():
    a, b, cor = cfg["a"], cfg["b"], cfg["cor"]
    q = max(0.0, a - b * preco)
    E = E_pontual(a, b, preco)
    linhas.append((nome, q, E, cor, a, b, choke_price(a,b)))

# ------------------ CARDS (DESTAQUES) ------------------
st.markdown("### Resultados no preço atual")
c1, c2, c3 = st.columns(3)
cards = [c1, c2, c3]
for col, (nome, q, E, cor, a, b, cp) in zip(cards, linhas):
    with col:
        box = f"""
        <div style="
            background:#f7f9fc; border:1px solid #e5eaf1; border-radius:14px;
            padding:14px 16px;">
            <div style="font-weight:700; color:#111827; font-size:16px;">{nome}</div>
            <div style="display:flex; gap:18px; margin-top:8px; flex-wrap:wrap;">
                <div>
                    <div style="font-size:12px; color:#6b7280;">Quantidade</div>
                    <div style="font-size:22px; font-weight:700; color:#111827;">{q:.1f}</div>
                </div>
                <div>
                    <div style="font-size:12px; color:#6b7280;">|E|</div>
                    <div style="font-size:22px; font-weight:700; color:#111827;">{('-' if E is None else f'{abs(E):.2f}')}</div>
                </div>
                <div>
                    <div style="font-size:12px; color:#6b7280;">Classe</div>
                    <div style="font-size:14px; font-weight:700; color:{cor};">{classif(E)}</div>
                </div>
                <div>
                    <div style="font-size:12px; color:#6b7280;">Interceptos</div>
                    <div style="font-size:13px; color:#111827;">Q(0)=<b>{a:.1f}</b> • P*=<b>{cp:.1f}</b></div>
                </div>
            </div>
        </div>
        """
        st.markdown(box, unsafe_allow_html=True)

st.info(f"Preço selecionado: **R$ {preco}**")

# ------------------ GRÁFICO DE CURVAS PRECISAS ------------------
# Domínio dinâmico de P
min_p = 0
max_cp = max(choke_price(a,b) for _,_,_,_,a,b,_ in linhas)
max_p = max(max(100, preco*1.1), max_cp*1.05)
P = np.linspace(min_p, max_p, 1200)

# Padding para as anotações (evita sobreposição)
max_q0 = max(a_est, a_emp, a_fam)
y_pad_pt   = max_q0 * 0.025   # p/ texto do ponto atual
y_pad_q0   = max_q0 * 0.035   # p/ Q(0)
y_top_extra = max_q0 * 0.18   # aumenta espaço no topo

fig, ax = plt.subplots(figsize=(9.8, 5.6))
fig.patch.set_facecolor(COL_BG_DARK)
ax.set_facecolor(COL_AX_DARK)

for (nome, q_atual, E, cor, a, b, cp) in linhas:
    Q_raw_vals = Q_raw(a, b, P)
    mask_pos = Q_raw_vals >= 0
    # Parte inviável (Q<0) pontilhada
    if np.any(~mask_pos):
        ax.plot(P[~mask_pos], Q_raw_vals[~mask_pos],
                color=cor, linewidth=1.3, linestyle=":", alpha=0.35, antialiased=True)
    # Parte viável (Q>=0)
    ax.plot(P[mask_pos], Q_raw_vals[mask_pos],
            label=f"Demanda – {nome}", color=cor, linewidth=2.4, antialiased=True)
    # Ponto no preço atual
    ax.scatter([preco], [q_atual], color=cor, s=70, zorder=5)
    # Valor do ponto com offset e caixa
    if q_atual > 0:
        ax.text(preco, q_atual + y_pad_pt, f"{q_atual:.1f}",
                color=COL_LABEL, va="bottom", ha="center", fontsize=10,
                bbox=dict(facecolor=COL_BG_DARK, alpha=0.65, edgecolor="none", pad=1.5))
    else:
        # Se Q=0 no preço atual, escreve um pouco acima do eixo
        ax.text(preco, 0 + y_pad_pt, f"{q_atual:.1f}",
                color=COL_LABEL, va="bottom", ha="center", fontsize=10,
                bbox=dict(facecolor=COL_BG_DARK, alpha=0.65, edgecolor="none", pad=1.5))

# Linha do preço atual
ax.axvline(preco, color=COL_PRICE, linestyle="--", linewidth=1.5, label="Preço selecionado")

# Interceptos (com offset e caixa)
for (nome, q_atual, E, cor, a, b, cp) in linhas:
    # Q(0)=a
    ax.scatter([0], [a], color=cor, s=40, zorder=4)
    ax.text(0, a + y_pad_q0, f"Q(0)={a:.1f}",
            color=COL_LABEL, va="bottom", ha="left", fontsize=10,
            bbox=dict(facecolor=COL_BG_DARK, alpha=0.65, edgecolor="none", pad=1.5))
    # P* = a/b
    ax.scatter([cp], [0], color=cor, s=40, zorder=4)
    ax.text(cp, 0 + y_pad_pt, f"P*={cp:.1f}",
            color=COL_LABEL, va="bottom", ha="center", fontsize=10,
            bbox=dict(facecolor=COL_BG_DARK, alpha=0.65, edgecolor="none", pad=1.5))

# Estilo e limites
ax.grid(color=COL_GRID, linestyle=":", linewidth=0.8, alpha=0.7)
ax.set_xlabel("Preço (R$)", color=COL_LABEL)
ax.set_ylabel("Quantidade Demandada", color=COL_LABEL)
ax.set_title("Curvas de Demanda por Perfil (alta resolução, interceptos e ponto atual)",
             color=COL_TITLE, pad=10, fontsize=18)
ax.tick_params(colors=COL_LABEL)

# Limites Y com folga extra p/ anotações
ax.set_ylim(bottom=0, top=max(max_q0 + y_top_extra, 10))
ax.set_xlim(left=0, right=max_p)

# Legenda
leg = ax.legend(facecolor="#1a1f2e", edgecolor="#2a3146")
for text in leg.get_texts():
    text.set_color("#e6e6e6")

st.pyplot(fig, use_container_width=True)

# ------------------ DOWNLOAD DO GRÁFICO ------------------
buf = BytesIO()
fig.savefig(buf, format="png", dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
st.download_button("⤓ Baixar gráfico (PNG)", data=buf.getvalue(),
                   file_name="curvas_demanda_precisas.png", mime="image/png")

# ------------------ TABELA ------------------
st.markdown("### Tabela (quantidades, elasticidades e parâmetros no preço atual)")
df = pd.DataFrame([{
    "Perfil": n,
    "Quantidade (Q)": round(q, 1),
    "Elasticidade (|E|)": "-" if E is None else f"{abs(E):.2f}",
    "Classificação": classif(E),
    "Q(0)=a": round(a, 2),
    "P* = a/b": round(cp, 2),
    "b (inclinação)": round(b, 2),
} for n, q, E, c, a, b, cp in linhas])
st.dataframe(df, use_container_width=True)

# ------------------ EXPLICANDO A IA ------------------
with st.expander("Como usamos IA generativa neste artefato"):
    st.markdown("""
- **ChatGPT** ajudou a gerar/refinar o código em **Python + Streamlit**, calcular **elasticidade pontual** e ajustar o layout.
- Melhorias de precisão: curvas com **alta resolução**, **interceptos** destacados, **offset** e **caixas** nas anotações para evitar sobreposição.
- Resultado: leitura clara em projetor e valores sempre legíveis.
""")
