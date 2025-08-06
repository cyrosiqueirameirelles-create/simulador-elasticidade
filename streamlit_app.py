
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador de Elasticidade-Preço", layout="centered")

st.title("📊 Simulador de Elasticidade-Preço da Demanda")

st.markdown("""
Este simulador interativo mostra como diferentes **perfis de consumidores** reagem a mudanças no preço de um produto, com base no conceito de **elasticidade-preço da demanda**.
""")

def calcular_demanda(preco, perfil):
    if perfil == "Estudante":
        return max(0, 100 - 2.5 * preco)
    elif perfil == "Família":
        return max(0, 80 - 1.2 * preco)
    elif perfil == "Empresa":
        return max(0, 60 - 0.5 * preco)

perfil = st.selectbox("👤 Selecione o perfil do consumidor:", ["Estudante", "Família", "Empresa"])
preco = st.slider("💰 Ajuste o preço do produto (R$)", min_value=10, max_value=100, step=1)

qtd = calcular_demanda(preco, perfil)

st.success(f"📦 Quantidade demandada pelo perfil **{perfil}** com preço R$ {preco}: **{int(qtd)} unidades**")

precos = list(range(10, 101, 1))
quantidades = [calcular_demanda(p, perfil) for p in precos]

fig, ax = plt.subplots()
ax.plot(precos, quantidades, label=f'Demanda - {perfil}', color='blue')
ax.axvline(preco, color='red', linestyle='--', label='Preço Atual')
ax.axhline(qtd, color='green', linestyle='--', label='Qtd Demandada')
ax.set_xlabel("Preço (R$)")
ax.set_ylabel("Quantidade Demandada")
ax.set_title("Curva de Demanda Individual")
ax.legend()
ax.grid(True)

st.pyplot(fig)
