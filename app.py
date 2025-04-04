
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

FRED_API_KEY = "f4b558fccbf4b6b5104773899e01ed10"

def buscar_ipca_fred(api_key):
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FPCPITOTLZGBRA&api_key={api_key}&file_type=json&observation_start=2023-01-01"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            valores = [float(obs['value']) for obs in data['observations'] if obs['value'] != "."]
            if valores:
                media_anual = sum(valores[-12:]) / 12
                return media_anual
    except Exception as e:
        st.warning(f"Erro ao buscar IPCA no FRED: {e}")
    return None

def buscar_selic_brasilapi():
    try:
        url = "https://brasilapi.com.br/api/taxas/v1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            taxas = response.json()
            for t in taxas:
                if t['nome'].lower() == 'selic':
                    return float(t['valor'])
    except Exception as e:
        st.warning(f"Erro ao buscar SELIC na BrasilAPI: {e}")
    return None

def calcular_detalhado(capital_inicial, taxa_mensal, meses_total, valor_mensal, meses_movimentacao, tipo_movimento):
    taxa = taxa_mensal / 100
    saldo = capital_inicial
    dados = []

    for mes in range(meses_total + 1):
        if mes == 0:
            dividendos = 0
            movimento = 0
        else:
            dividendos = saldo * taxa
            saldo += dividendos

            if tipo_movimento == "aportes" and mes <= meses_movimentacao:
                movimento = valor_mensal
                saldo += valor_mensal
            elif tipo_movimento == "retiradas" and mes <= meses_movimentacao:
                movimento = -valor_mensal
                saldo -= valor_mensal
            else:
                movimento = 0

        dados.append({
            "Mês": mes,
            "Dividendos (R$)": round(dividendos, 2),
            "Aporte/Retirada (R$)": round(movimento, 2),
            "Valor Reinvestido (R$)": round(saldo, 2)
        })

    return pd.DataFrame(dados)

def main():
    st.title("📈 Simulador de Investimentos com Juros Compostos")

    capital = st.number_input("💵 Capital inicial (R$)", value=10000.0, min_value=0.0)
    meses = st.number_input("⏳ Total de meses", value=240, min_value=1)
    tipo = st.selectbox("💼 Tipo de movimentação", ["nenhum", "aportes", "retiradas"])
    valor_mensal = st.number_input("💸 Valor mensal (R$)", value=1000.0)
    meses_mov = st.slider("📆 Meses com movimentação", min_value=0, max_value=600, value=12)
    mostrar_grafico = st.checkbox("📊 Mostrar gráfico de evolução", value=True)

    indexador = st.selectbox("📊 Escolha o indexador:", [
        "Taxa personalizada (%)",
        "SELIC (via BrasilAPI)",
        "IPCA (via FRED)"
    ])

    taxa_final = 1.0

    if indexador == "Taxa personalizada (%)":
        taxa_final = st.number_input("📉 Informe a taxa personalizada (% ao mês)", value=1.0, min_value=0.0)
    elif indexador == "SELIC (via BrasilAPI)":
        taxa_selic = buscar_selic_brasilapi()
        if taxa_selic:
            taxa_final = ((1 + taxa_selic / 100) ** (1 / 12) - 1) * 100
            st.info(f"📌 SELIC anual: {taxa_selic:.2f}% → mensal composta: {taxa_final:.4f}%")
        else:
            st.error("Erro ao obter SELIC. Usando taxa padrão de 1% ao mês.")
            taxa_final = 1.0
    elif indexador == "IPCA (via FRED)":
        taxa_ipca = buscar_ipca_fred(FRED_API_KEY)
        if taxa_ipca:
            taxa_final = ((1 + taxa_ipca / 100) ** (1 / 12) - 1) * 100
            st.info(f"📌 IPCA anual: {taxa_ipca:.2f}% → mensal composta: {taxa_final:.4f}%")
        else:
            st.error("Erro ao obter IPCA. Usando taxa padrão de 1% ao mês.")
            taxa_final = 1.0

    if st.button("Calcular"):
        df = calcular_detalhado(capital, taxa_final, meses, valor_mensal, meses_mov, tipo)
        valor_final = df.iloc[-1]["Valor Reinvestido (R$)"]
        st.success(f"💰 Valor final ao fim de {meses} meses: R$ {valor_final:,.2f}")

        if mostrar_grafico:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(df["Mês"], df["Valor Reinvestido (R$)"], marker='o')
            ax.set_title("Evolução do Capital")
            ax.set_xlabel("Mês")
            ax.set_ylabel("Saldo (R$)")
            ax.grid(True)
            st.pyplot(fig)

        st.subheader("📋 Detalhamento Mês a Mês")
        st.dataframe(df)

if __name__ == "__main__":
    main()
