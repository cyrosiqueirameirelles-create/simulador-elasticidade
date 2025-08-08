import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Simulador de Elasticidade-Preço", layout="wide")

# ======= TÍTULO E INTRO =======
st.title("📊 Simulador de Elasticidade-Preço da Demanda (3 perfis)")
st.write(
    "Este simulador mostra como **perfis de consumidores** reagem a mudanças no preço, "
    "com base na **elasticidade-preço da demanda**. Ajuste o preço e veja as "
    "**quantidades** e **elasticidades** para Estudante, Família e Empresa."
)

# ======= PARÂMETROS DOS PERFIS (Q = a - bP) =======
perfis = {
    "Estudante": {"a": 100, "b": 2.5, "cor": "#f7b500"},  # amarelo
    "Empresa":   {"a":  60, "b": 0.5, "cor": "#3aa0ff"},  # azul
    "Família":   {"a":  80, "b": 1.2, "cor": "#38d39f"},  # verde
}

# ======= CONTROLE DE PREÇO =======
preco = st.slider("💰 Preço do produto (R$)", min_value=10, max_value=100, value=25, step=1)

# ======= FUNÇÕES =======
def quantidade(a, b, p):
    return max(0, a - b * p)

def elasticidade_pontual(a, b, p):
    q = quantidade(a, b, p)
    if q == 0:
        return None
    # E = (dQ/dP)*(P/Q) = (-b)*(P/Q) para demanda linear
    return -b * (p / q)

def classifica_e(E):
    if E is None:
        return "sem demanda"
    e_abs = abs(E)
    if e_abs > 1:
        return "elástica (>1)"
    if e_abs < 1:
        return "inelástica (<1)"
    return "unitária (=1)"

# ======= CÁLCULOS =======
precos = list(range(10, 101, 1))
series = {}
linhas_info = []
for nome, cfg in perfis.items():
    a, b, cor = cfg["a"], cfg["b"], cfg["cor"]
    qs = [quantidade(a, b, p) for p in precos]
    q_atual = quantidade(a, b, preco)
    e_atual = elasticidade_pontual(a, b, preco)
    series[nome] = {"precos": precos, "qs": qs, "q_atual": q_atual, "E": e_atual, "cor": cor}
    linhas_info.append((nome, q_atual, e_atual, cor))

# ======= RESUMO NO TOPO (TEXTO ESCURO PADRÃO) =======
resumo = " • ".join(
    [f"**{nome}**: Q = **{int(q)}** {'' if E is None else f'| E={E:.2f} ({classifica_e(E)})'}"
     for nome, q, E, _ in linhas_info]
)
st.info(f"Preço selecionado: R$ {preco}  |  {resumo}")

# ======= GRÁFICO (TEMA ESCURO) =======
fig, ax = plt.subplots(figsize=(9, 5))
fig.patch.set_facecolor("#0f1116")
ax.set_facecolor("#0f1116")

for nome, dados in series.items():
    ax.plot(dados["precos"], dados["qs"], label=f"Demanda – {nome}",
            color=dados["cor"], linewidth=2.2)
    ax.scatter([preco], [dados["q_atual"]], color=dados["cor"], s=60, zorder=5)

ax.axvline(preco, color="#c33d3d", linestyle="--", linewidth=1.4, label="Preço selecionado")

# Estilo do gráfico (cores claras só dentro do gráfico)
ax.grid(color="#2a3146", linestyle=":", linewidth=0.8, alpha=0.7)
ax.set_xlabel("Preço (R$)", color="#cfd6e6")
ax.set_ylabel("Quantidade Demandada", color="#cfd6e6")
ax.set_title("Curvas de Demanda por Perfil", color="#ffffff", pad=10, fontsize=18)
ax.tick_params(colors="#cfd6e6")
leg = ax.legend(facecolor="#1a1f2e", edgecolor="#2a3146")
for text in leg.get_texts():
    text.set_color("#e6e6e6")

st.pyplot(fig, use_container_width=True)

# ======= TABELA (FUNDO BRANCO, TEXTO ESCURO) =======
st.subheader("Quantidades e elasticidades no preço atual")
linhas_tabela = []
for nome, q, E, cor in linhas_info:
    linhas_tabela.append({
        "Perfil": nome,
        "Quantidade": int(q),
        "Elasticidade (E)": "-" if E is None else f"{E:.2f}",
        "Classificação": classifica_e(E)
    })
df = pd.DataFrame(linhas_tabela)
st.dataframe(df, use_container_width=True)

# ======= EXPLICAÇÃO DE USO DE IA (PROFESSOR PEDIU) =======
with st.expander("Como usamos IA generativa neste artefato"):
    st.markdown("""
- **ChatGPT** foi usado para gerar o código base em **Python + Streamlit**, criar o gráfico com **Matplotlib**, 
  calcular **elasticidade pontual** e estilizar a interface.
- Iteramos prompts para:
  - Exibir **todas as curvas** no mesmo gráfico, com marcadores no **preço selecionado**;
  - Gerar **resumos automáticos** com quantidades e elasticidades;
  - Ajustar o **layout** para boa leitura em projetor (gráfico escuro) e em áreas brancas (tabela e caixas com texto escuro).
- O resultado é um **artefato interativo** que transforma o conceito de elasticidade-preço em uma ferramenta visual e funcional.
""")
